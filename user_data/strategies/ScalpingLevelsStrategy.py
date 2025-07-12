# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file

"""
Scalping Levels Strategy - Based on Professional Trading Video
=============================================================

Core Concept: 15-minute narrative + 1-minute entries + 5-minute risk management
- 15m timeframe: Identify key levels (previous day high/low, previous day close, opening print)
- 1m timeframe: Enter on breaks and retests of these levels
- Risk management: Stop just outside key levels, scale out at targets

Key Levels (only these matter):
1. Previous day high
2. Previous day low  
3. Previous day close
4. Opening print
5. Only look back 3-5 sessions (1 week max)

Entry Logic:
- Wait for break above/below key level
- Enter on RETEST of broken level (don't chase)
- Quick decision making - know immediately if wrong

Risk Management:
- Stop just outside the key level
- Scale out at 1:2 first target
- Trail remaining position
- Maximum 24h hold time

Target Performance: 
- Higher win rate than current 23.1%
- More trades than current 681
- Cleaner signals, less noise
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
from pandas import DataFrame

import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy, merge_informative_pair

class ScalpingLevelsStrategy(IStrategy):
    """
    Professional scalping strategy based on key levels from higher timeframes.
    Uses 15m narrative, 1m entries, 5m risk management.
    """

    INTERFACE_VERSION = 3
    timeframe: str = "1m"
    can_short: bool = False

    # Minimal startup - we only need basic indicators
    startup_candle_count: int = 200

    # No static ROI - we manage exits dynamically
    minimal_roi: Dict[str, float] = {}

    # Emergency stoploss
    stoploss: float = -0.10  # 10% hard floor

    # Trailing handled by custom_exit
    trailing_stop = False

    # ---------------------------------------------------------------------
    # Configuration
    # ---------------------------------------------------------------------
    # Key levels calculation periods
    LOOKBACK_SESSIONS = 5  # Look back 5 sessions max (1 week)
    
    # Risk management
    RISK_REWARD_RATIO = 1.5  # 1:1.5 ratio (was 2.0)
    MAX_HOLD_HOURS = 12  # Shorter hold time (was 24)
    
    # Entry confirmation
    MIN_VOLUME_RATIO = 1.5  # Higher volume requirement (was 1.2)
    ATR_PERIOD = 14  # For dynamic stops

    # ------------------------------------------------------------------
    # Informative pairs - get 15m data for key levels
    # ------------------------------------------------------------------
    def informative_pairs(self) -> List[Tuple[str, str]]:
        pairs = []
        if self.dp and self.dp.current_whitelist():
            for pair in self.dp.current_whitelist():
                pairs.append((pair, "15m"))
        return pairs

    # ------------------------------------------------------------------
    # Indicators
    # ------------------------------------------------------------------
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Simple indicators - we focus on price action, not complex indicators
        """
        # ATR for dynamic stops
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=self.ATR_PERIOD)
        
        # Volume moving average for confirmation
        dataframe["volume_sma"] = ta.SMA(dataframe['volume'], timeperiod=20)
        
        # Calculate key levels directly on the main dataframe
        dataframe = self.calculate_key_levels(dataframe)
        
        # Get 15m data for additional confirmation if available
        if self.dp and metadata:
            try:
                informative_15m = self.dp.get_pair_dataframe(
                    pair=metadata["pair"], 
                    timeframe="15m"
                )
                
                # Simple 15m trend confirmation
                informative_15m['ema_15m'] = ta.EMA(informative_15m, timeperiod=21)
                informative_15m['trend_15m'] = informative_15m['close'] > informative_15m['ema_15m']
                
                # Merge back to 1m
                dataframe = merge_informative_pair(
                    dataframe, informative_15m, self.timeframe, "15m", ffill=True
                )
                
                # If merge failed, create default values
                if 'trend_15m_15m' not in dataframe.columns:
                    dataframe['trend_15m_15m'] = True
                    
            except Exception:
                # If 15m data not available, create default values
                dataframe['trend_15m_15m'] = True

        return dataframe

    def calculate_key_levels(self, df: DataFrame) -> DataFrame:
        """
        Calculate key levels: previous day high, low, close, opening print
        Simplified approach for FreqTrade compatibility
        """
        # Rolling high/low over different periods to simulate daily levels
        df['prev_day_high'] = df['high'].rolling(window=1440, min_periods=1).max().shift(1)  # 1440 minutes = 1 day
        df['prev_day_low'] = df['low'].rolling(window=1440, min_periods=1).min().shift(1)
        df['prev_day_close'] = df['close'].shift(1440)  # Previous day close
        
        # Opening print - use a simpler approach
        # Just use the opening price of each candle as a proxy
        df['opening_print'] = df['open']
        
        # Fill NaN values with current values to avoid errors
        df['prev_day_high'] = df['prev_day_high'].fillna(df['high'])
        df['prev_day_low'] = df['prev_day_low'].fillna(df['low'])
        df['prev_day_close'] = df['prev_day_close'].fillna(df['close'])
        df['opening_print'] = df['opening_print'].fillna(df['open'])
        
        # Calculate distance to key levels (for entry filtering)
        df['dist_to_prev_high'] = abs(df['close'] - df['prev_day_high']) / df['prev_day_high']
        df['dist_to_prev_low'] = abs(df['close'] - df['prev_day_low']) / df['prev_day_low']
        df['dist_to_prev_close'] = abs(df['close'] - df['prev_day_close']) / df['prev_day_close']
        df['dist_to_opening'] = abs(df['close'] - df['opening_print']) / df['opening_print']
        
        # Boolean flags for being near key levels (within 0.5%)
        df['near_prev_high'] = df['dist_to_prev_high'] < 0.005
        df['near_prev_low'] = df['dist_to_prev_low'] < 0.005
        df['near_prev_close'] = df['dist_to_prev_close'] < 0.005
        df['near_opening'] = df['dist_to_opening'] < 0.005
        
        return df

    # ------------------------------------------------------------------
    # Entry Logic - Clean and Simple
    # ------------------------------------------------------------------
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Simplified entry logic based on key level breaks
        """
        # Volume must be above average
        volume_ok = dataframe['volume'] > dataframe['volume_sma'] * self.MIN_VOLUME_RATIO
        
        # Price action signals
        bullish_candle = dataframe['close'] > dataframe['open']
        price_rising = dataframe['close'] > dataframe['close'].shift(1)
        
        # Key level breakout scenarios (simplified)
        # 1. Above previous day high and holding
        above_prev_high = (
            (dataframe['close'] > dataframe['prev_day_high']) &
            (dataframe['low'] > dataframe['prev_day_high'] * 0.998) &  # Not too far below
            bullish_candle
        )
        
        # 2. Above previous day close and holding
        above_prev_close = (
            (dataframe['close'] > dataframe['prev_day_close']) &
            (dataframe['low'] > dataframe['prev_day_close'] * 0.998) &
            bullish_candle
        )
        
        # 3. Bounce from previous day low
        bounce_from_low = (
            (dataframe['low'] <= dataframe['prev_day_low'] * 1.002) &  # Touch the low
            (dataframe['close'] > dataframe['prev_day_low'] * 1.005) &  # Close above
            bullish_candle &
            price_rising
        )
        
        # 4. Break above opening print
        above_opening = (
            (dataframe['close'] > dataframe['opening_print']) &
            (dataframe['low'] > dataframe['opening_print'] * 0.998) &
            bullish_candle
        )
        
        # Must be near a key level to avoid random entries
        near_key_level = (
            dataframe['near_prev_high'] | 
            dataframe['near_prev_low'] | 
            dataframe['near_prev_close'] | 
            dataframe['near_opening']
        )
        
        # Combine all conditions
        entry_conditions = (
            above_prev_high | above_prev_close | bounce_from_low | above_opening
        )
        
        final_entry = volume_ok & entry_conditions & near_key_level
        
        dataframe.loc[final_entry, "enter_long"] = 1
        return dataframe

    # ------------------------------------------------------------------
    # Exit Logic - Let custom_exit handle everything
    # ------------------------------------------------------------------
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        No exit signals - we handle everything in custom_exit for precise control
        """
        return dataframe

    # ------------------------------------------------------------------
    # Dynamic Stop Loss
    # ------------------------------------------------------------------
    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs):
        """
        Simplified dynamic stop loss based on ATR
        """
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return 1
        
        # Get current ATR
        atr = dataframe["atr"].iloc[-1]
        if atr == 0:
            return 1
        
        # Simple ATR-based stop
        entry_price = trade.open_rate
        stop_price = entry_price - (atr * 1.0)  # 1.0 ATR stop (was 1.5)
        
        # Calculate stop loss percentage
        stop_loss_pct = (entry_price - stop_price) / entry_price
        
        # Ensure reasonable stop loss (between 0.3% and 2%)
        stop_loss_pct = max(0.003, min(0.02, stop_loss_pct))
        
        # Check if stop should trigger
        if current_profit <= -stop_loss_pct:
            return 0.01  # Trigger stop
        
        return 1  # No change

    # ------------------------------------------------------------------
    # Custom Exit - Scale out and trail
    # ------------------------------------------------------------------
    def custom_exit(self, pair: str, trade: Trade, current_time: datetime,
                    current_rate: float, current_profit: float, **kwargs):
        """
        Simplified exit management based on video approach:
        1. Take profit at 1:2 ratio
        2. Time-based exit
        3. Trail if profitable
        """
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return None

        # Get ATR for target calculation
        atr = dataframe["atr"].iloc[-1]
        if atr == 0:
            return None
        
        # Calculate basic targets
        entry_price = trade.open_rate
        target_1 = entry_price + (atr * self.RISK_REWARD_RATIO)  # 1:2 ratio
        
        # Trade duration
        trade_duration = (current_time - trade.open_date).total_seconds() / 3600  # hours
        
        # Time-based exit (video emphasizes quick decisions)
        if trade_duration > self.MAX_HOLD_HOURS:
            return {
                "exit_tag": "max_time",
                "exit_type": "exit_signal",
            }
        
        # Take profit at target
        if current_rate >= target_1:
            return {
                "exit_tag": "target_reached",
                "exit_type": "exit_signal",
            }
        
        # Simple trailing stop if we've been profitable
        if current_profit > 0.01 and trade.max_rate is not None:
            trail_distance = atr * 0.8  # Trail with 0.8 ATR
            trail_stop = trade.max_rate - trail_distance
            
            if current_rate <= trail_stop:
                return {
                    "exit_tag": "trail_stop",
                    "exit_type": "exit_signal",
                }
        
        # Exit if we're losing too much time (video emphasizes knowing when wrong)
        if trade_duration > 1 and current_profit < -0.005:  # 1 hour and losing 0.5% (was 2h, 1%)
            return {
                "exit_tag": "quick_exit",
                "exit_type": "exit_signal",
            }
        
        # Take partial profit earlier for scalping
        if current_profit > 0.005:  # 0.5% profit
            return {
                "exit_tag": "scalp_profit",
                "exit_type": "exit_signal",
            }
        
        return None 