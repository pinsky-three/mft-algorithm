# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file

"""
Crypto Scalping Hybrid Strategy - Best of Both Worlds
====================================================

Combines:
1. Video's Key Levels Approach (15m narrative + precise entries)
2. Original Momentum Filters (EMA + RSI + Volume)
3. Crypto-Specific Adaptations (24/7 markets, volatility patterns)

Core Concept:
- 15m timeframe: Identify key levels + trend direction
- 5m timeframe: Enter on momentum + key level confluence  
- Risk management: 1:3 ratio, crypto-optimized stops

Key Improvements:
✅ Higher profit targets (crypto volatility)
✅ Momentum confirmation (trend following)
✅ Fewer, higher quality trades
✅ Crypto market adaptations
✅ Better risk/reward ratios

Expected Performance:
- Win rate: 60-70% (balanced)
- Return: Positive (goal: beat market)
- Trades: 1000-2000 (quality over quantity)
- Duration: 2-6 hours (true scalping)
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

class CryptoScalpingHybrid(IStrategy):
    """
    Hybrid scalping strategy combining key levels with momentum filters.
    Designed specifically for 24/7 crypto markets.
    """

    INTERFACE_VERSION = 3
    timeframe: str = "5m"  # 5m for better quality signals
    can_short: bool = False

    # Reasonable startup for both indicators
    startup_candle_count: int = 300

    # No static ROI - dynamic exits only
    minimal_roi: Dict[str, float] = {}

    # Conservative emergency stop
    stoploss: float = -0.08  # 8% hard floor

    # Custom trailing via exits
    trailing_stop = False

    # ---------------------------------------------------------------------
    # Hybrid Strategy Configuration
    # ---------------------------------------------------------------------
    
    # Risk Management (Crypto-optimized)
    RISK_REWARD_RATIO = 3.0  # 1:3 minimum for crypto
    MAX_HOLD_HOURS = 8  # Reasonable for 5m scalping
    STOP_LOSS_ATR = 1.2  # Tighter stops
    
    # Key Levels (from video)
    LOOKBACK_SESSIONS = 3  # Shorter lookback for crypto
    LEVEL_PROXIMITY = 0.008  # 0.8% proximity to levels
    
    # Momentum Filters (from original)
    MIN_VOLUME_RATIO = 1.8  # Strong volume requirement
    RSI_THRESHOLD = 55  # Balanced momentum
    
    # Crypto-specific
    VOLATILITY_FILTER = True  # Only trade in volatile periods
    MIN_ATR_RATIO = 0.002  # Minimum 0.2% ATR for trade

    # ------------------------------------------------------------------
    # Informative pairs - get 15m for key levels + trend
    # ------------------------------------------------------------------
    def informative_pairs(self) -> List[Tuple[str, str]]:
        pairs = []
        if self.dp and self.dp.current_whitelist():
            for pair in self.dp.current_whitelist():
                pairs.append((pair, "15m"))  # For key levels and trend
        return pairs

    # ------------------------------------------------------------------
    # Indicators - Hybrid approach
    # ------------------------------------------------------------------
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Hybrid indicators combining momentum and key levels
        """
        # === Momentum Indicators (from original) ===
        # EMA stack for trend
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=12)   # 1h on 5m
        dataframe["ema_mid"] = ta.EMA(dataframe, timeperiod=24)    # 2h on 5m  
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=48)   # 4h on 5m
        
        # RSI for momentum
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        
        # MACD for trend strength
        macd = ta.MACD(dataframe)
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]
        
        # ATR for volatility and stops
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        
        # Volume analysis
        dataframe["volume_sma"] = ta.SMA(dataframe['volume'], timeperiod=20)
        dataframe["volume_ratio"] = dataframe['volume'] / dataframe["volume_sma"]
        
        # === Key Levels (from video approach) ===
        dataframe = self.calculate_crypto_levels(dataframe)
        
        # === 15m Context ===
        if self.dp and metadata:
            try:
                informative_15m = self.dp.get_pair_dataframe(
                    pair=metadata["pair"], 
                    timeframe="15m"
                )
                
                # 15m trend confirmation
                informative_15m['ema_15m'] = ta.EMA(informative_15m, timeperiod=21)
                informative_15m['ema_50_15m'] = ta.EMA(informative_15m, timeperiod=50)
                informative_15m['trend_15m'] = (
                    (informative_15m['ema_15m'] > informative_15m['ema_50_15m']) &
                    (informative_15m['close'] > informative_15m['ema_15m'])
                )
                
                # 15m key levels
                informative_15m = self.calculate_crypto_levels(informative_15m)
                
                # Merge to 5m
                dataframe = merge_informative_pair(
                    dataframe, informative_15m, self.timeframe, "15m", ffill=True
                )
                
            except Exception:
                # Default values if 15m data unavailable
                dataframe['trend_15m_15m'] = True
                dataframe['prev_session_high_15m'] = dataframe['high']
                dataframe['prev_session_low_15m'] = dataframe['low']

        # === Hybrid Signals ===
        # Momentum alignment
        dataframe['momentum_aligned'] = (
            (dataframe["ema_fast"] > dataframe["ema_mid"]) &
            (dataframe["ema_mid"] > dataframe["ema_slow"]) &
            (dataframe["rsi"] > self.RSI_THRESHOLD) &
            (dataframe["macd"] > dataframe["macdsignal"])
        )
        
        # Volatility filter
        if self.VOLATILITY_FILTER:
            dataframe['volatile_enough'] = (
                dataframe["atr"] / dataframe["close"] > self.MIN_ATR_RATIO
            )
        else:
            dataframe['volatile_enough'] = True
            
        # Volume confirmation
        dataframe['volume_confirmed'] = (
            dataframe["volume_ratio"] > self.MIN_VOLUME_RATIO
        )

        return dataframe

    def calculate_crypto_levels(self, df: DataFrame) -> DataFrame:
        """
        Calculate crypto-adapted key levels
        Uses session-based approach adapted for 24/7 markets
        """
        # Crypto "sessions" - 8-hour periods
        session_length = 96 if len(df) > 1000 else 48  # 8h for 5m, 4h for 15m
        
        # Rolling session highs/lows
        df['prev_session_high'] = df['high'].rolling(
            window=session_length, min_periods=12
        ).max().shift(1)
        
        df['prev_session_low'] = df['low'].rolling(
            window=session_length, min_periods=12
        ).min().shift(1)
        
        df['prev_session_close'] = df['close'].shift(session_length)
        
        # Session open (approximate) - use a simpler approach
        df['session_open'] = df['open']
        
        # Fill NaN values
        for col in ['prev_session_high', 'prev_session_low', 'prev_session_close', 'session_open']:
            if col not in df.columns:
                continue
            df[col] = df[col].ffill().fillna(df['close'])
        
        # Level proximity
        df['near_session_high'] = (
            abs(df['close'] - df['prev_session_high']) / df['prev_session_high'] < self.LEVEL_PROXIMITY
        )
        df['near_session_low'] = (
            abs(df['close'] - df['prev_session_low']) / df['prev_session_low'] < self.LEVEL_PROXIMITY
        )
        df['near_session_close'] = (
            abs(df['close'] - df['prev_session_close']) / df['prev_session_close'] < self.LEVEL_PROXIMITY
        )
        
        return df

    # ------------------------------------------------------------------
    # Hybrid Entry Logic
    # ------------------------------------------------------------------
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Hybrid entry: Key levels + Momentum confirmation
        """
        
        # === Core Filters ===
        momentum_ok = dataframe['momentum_aligned']
        volume_ok = dataframe['volume_confirmed'] 
        volatility_ok = dataframe['volatile_enough']
        
        # 15m trend confirmation
        trend_15m_ok = dataframe.get('trend_15m_15m', True)
        
        # === Key Level Scenarios ===
        
        # 1. Break above previous session high with momentum
        break_session_high = (
            (dataframe['close'] > dataframe['prev_session_high']) &
            (dataframe['close'].shift(1) <= dataframe['prev_session_high'].shift(1)) &
            (dataframe['close'] > dataframe['open'])  # Bullish candle
        )
        
        # 2. Bounce from previous session low with momentum
        bounce_session_low = (
            (dataframe['low'] <= dataframe['prev_session_low'] * 1.005) &  # Touch level
            (dataframe['close'] > dataframe['prev_session_low'] * 1.008) &  # Close above
            (dataframe['close'] > dataframe['open'])  # Bullish candle
        )
        
        # 3. Break above previous session close with strong momentum
        break_session_close = (
            (dataframe['close'] > dataframe['prev_session_close']) &
            (dataframe['close'].shift(1) <= dataframe['prev_session_close'].shift(1)) &
            (dataframe['rsi'] > 60)  # Strong momentum
        )
        
        # 4. Pullback to key level in uptrend
        pullback_buy = (
            trend_15m_ok &
            (dataframe['near_session_high'] | dataframe['near_session_close']) &
            (dataframe['close'] > dataframe['ema_fast']) &
            (dataframe['close'] > dataframe['open'])
        )
        
        # === Combine All Conditions ===
        key_level_signals = (
            break_session_high | bounce_session_low | 
            break_session_close | pullback_buy
        )
        
        # Final entry condition
        entry_condition = (
            momentum_ok & 
            volume_ok & 
            volatility_ok & 
            trend_15m_ok &
            key_level_signals
        )
        
        dataframe.loc[entry_condition, "enter_long"] = 1
        return dataframe

    # ------------------------------------------------------------------
    # No exit signals - custom_exit handles everything
    # ------------------------------------------------------------------
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    # ------------------------------------------------------------------
    # Dynamic Stop Loss
    # ------------------------------------------------------------------
    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs):
        """
        Crypto-optimized dynamic stop loss
        """
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return 1

        atr = dataframe["atr"].iloc[-1]
        if atr == 0:
            return 1

        # ATR-based stop with crypto optimization
        entry_price = trade.open_rate
        stop_distance = atr * self.STOP_LOSS_ATR
        stop_price = entry_price - stop_distance
        
        # Stop loss percentage
        stop_loss_pct = (entry_price - stop_price) / entry_price
        
        # Crypto-appropriate range (0.4% to 3%)
        stop_loss_pct = max(0.004, min(0.03, stop_loss_pct))
        
        # Trigger stop
        if current_profit <= -stop_loss_pct:
            return 0.01
        
        return 1

    # ------------------------------------------------------------------
    # Hybrid Exit Management
    # ------------------------------------------------------------------
    def custom_exit(self, pair: str, trade: Trade, current_time: datetime,
                    current_rate: float, current_profit: float, **kwargs):
        """
        Professional crypto exit management
        """
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return None

        atr = dataframe["atr"].iloc[-1]
        if atr == 0:
            return None

        # Trade info
        entry_price = trade.open_rate
        trade_duration = (current_time - trade.open_date).total_seconds() / 3600
        
        # === Profit Targets ===
        target_1 = entry_price + (atr * self.RISK_REWARD_RATIO * 0.5)  # First target
        target_2 = entry_price + (atr * self.RISK_REWARD_RATIO)        # Main target
        target_3 = entry_price + (atr * self.RISK_REWARD_RATIO * 1.5)  # Extension
        
        # === Exit Conditions ===
        
        # 1. Time-based exit
        if trade_duration > self.MAX_HOLD_HOURS:
            return {
                "exit_tag": "max_time",
                "exit_type": "exit_signal",
            }
        
        # 2. Take profit levels
        if current_rate >= target_2:
            return {
                "exit_tag": "main_target",
                "exit_type": "exit_signal",
            }
        elif current_rate >= target_1 and trade_duration > 2:  # First target after 2h
            return {
                "exit_tag": "first_target", 
                "exit_type": "exit_signal",
            }
        
        # 3. Trailing stop after reaching first target
        if (trade.max_rate is not None and 
            trade.max_rate >= target_1 and 
            current_profit > 0.01):
            
            trail_distance = atr * 0.8  # Crypto-appropriate trailing
            trail_stop = trade.max_rate - trail_distance
            
            if current_rate <= trail_stop:
                return {
                    "exit_tag": "trail_stop",
                    "exit_type": "exit_signal",
                }
        
        # 4. Quick exit if momentum fails
        if trade_duration > 1 and current_profit < -0.008:  # 1h and -0.8%
            return {
                "exit_tag": "momentum_fail",
                "exit_type": "exit_signal",
            }
        
        # 5. Momentum reversal exit
        current_data = dataframe.iloc[-1]
        if (current_profit > 0.005 and  # In profit
            not current_data.get('momentum_aligned', True)):  # Momentum gone
            return {
                "exit_tag": "momentum_exit",
                "exit_type": "exit_signal",
            }
        
        return None 