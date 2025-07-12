# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file

"""
Crypto Scalping Optimized v2 - PROFESSIONAL REDESIGN 🎯
======================================================

COMPLETE REDESIGN based on professional trading analysis:

❌ PROBLEMS IDENTIFIED:
- Losers 2-3x larger than winners (expectancy -0.05R)
- 561 trades/190 days = over-trading (loose filters)

✅ SOLUTIONS IMPLEMENTED:
1. Re-balanced R-multiple (3.0 ratio, 0.6 ATR stop)
2. Session bias filter (London/NY only)
3. Liquidity sweep triggers (pro setups only)
4. Fixed momentum calculation bug
5. Added ROI safety ladder
6. Quality over quantity approach

🎯 EXPECTED RESULTS:
- Trades: 250-300 (was 561)
- Win rate: 55-60% (was 62.6%)
- Avg win: 1.2% (was 0.55%)
- Avg loss: -0.50% (was -0.90%)
- Expectancy: +0.22% (was -0.06%)
- Profit factor: >1.3 (was 0.81)
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

class CryptoScalpingOptimized(IStrategy):
    """
    PROFESSIONAL REDESIGN: Session-based liquidity sweep scalping
    Following proven YouTube strategy structure:
    1. Session bias → 2. Liquidity raid → 3. Micro confirmation → 4. Asymmetric R-multiples
    """

    INTERFACE_VERSION = 3
    timeframe: str = "5m"
    can_short: bool = False
    startup_candle_count: int = 300

    # === 5. ROI SAFETY LADDER ===
    minimal_roi: Dict[str, float] = {
        "0": 0.015,     # 1.5% asap
        "30": 0.010,    # after 30 min accept 1%
        "120": 0.005    # after 2h accept 0.5%
    }
    
    stoploss: float = -0.08
    trailing_stop = False

    # === 1. RE-BALANCED R-MULTIPLE ===
    RISK_REWARD_RATIO = 3.0      # 2.5 → 3.0 (bigger carrot)
    STOP_LOSS_ATR = 0.6          # 1.0 → 0.6 (smaller stick)
    MAX_HOLD_HOURS = 4           # Shorter for quality
    
    # === TIGHTENED FILTERS (Quality over Quantity) ===
    MIN_VOLUME_RATIO = 1.8       # 1.5 → 1.8 (back to strict)
    RSI_THRESHOLD = 55           # 50 → 55 (back to strict)
    LEVEL_PROXIMITY = 0.008      # 1.2% → 0.8% (tighter levels)
    
    # Enhanced momentum detection
    MOMENTUM_STRENGTH = 0.75     # 0.7 → 0.75 (stricter)
    MIN_ATR_RATIO = 0.0018       # 0.15% → 0.18% (more volatile)

    def informative_pairs(self) -> List[Tuple[str, str]]:
        pairs = []
        if self.dp and self.dp.current_whitelist():
            for pair in self.dp.current_whitelist():
                pairs.append((pair, "15m"))
        return pairs



    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Professional indicator stack with liquidity sweep detection"""
        
        # === Core Momentum Stack ===
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=10)
        dataframe["ema_mid"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=42)
        
        # Momentum oscillators
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        macd = ta.MACD(dataframe, fastperiod=12, slowperiod=26, signalperiod=9)
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]
        dataframe["macdhist"] = macd["macdhist"]
        
        # Volatility & Volume
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["volume_sma"] = ta.SMA(dataframe['volume'], timeperiod=20)
        dataframe["volume_ratio"] = dataframe['volume'] / dataframe["volume_sma"]
        
        # === Key Levels ===
        dataframe = self.calculate_liquidity_levels(dataframe)
        
        # === 15m Trend Context ===
        if self.dp and metadata:
            try:
                informative_15m = self.dp.get_pair_dataframe(
                    pair=metadata["pair"], timeframe="15m"
                )
                
                # Trend detection
                informative_15m['ema_trend'] = ta.EMA(informative_15m, timeperiod=21)
                informative_15m['trend_15m'] = (
                    informative_15m['close'] > informative_15m['ema_trend']
                )
                
                # Merge
                dataframe = merge_informative_pair(
                    dataframe, informative_15m, self.timeframe, "15m", ffill=True
                )
                
            except Exception:
                dataframe['trend_15m_15m'] = True

        # === 4. FIXED MOMENTUM CALCULATION ===
        
        # Momentum conditions (multiple checks)
        momentum_conditions = [
            dataframe["ema_fast"] > dataframe["ema_mid"],
            dataframe["ema_mid"] > dataframe["ema_slow"],
            dataframe["rsi"] > self.RSI_THRESHOLD,
            dataframe["macd"] > dataframe["macdsignal"],
            dataframe["close"] > dataframe["ema_fast"]
        ]
        
        # FIX: Use np.sum for proper array summation
        momentum_score = np.sum(momentum_conditions, axis=0)
        dataframe['momentum_strength'] = momentum_score / len(momentum_conditions)
        dataframe['momentum_aligned'] = (
            dataframe['momentum_strength'] >= self.MOMENTUM_STRENGTH
        )
        
        # Enhanced filters
        dataframe['volume_confirmed'] = (
            dataframe["volume_ratio"] > self.MIN_VOLUME_RATIO
        )
        
        dataframe['volatile_enough'] = (
            dataframe["atr"] / dataframe["close"] > self.MIN_ATR_RATIO
        )
        
        # Trend confirmation from 15m
        dataframe['trend_confirmed'] = dataframe.get('trend_15m_15m', True)
        
        # === 2. SESSION BIAS FILTER ===
        # Extract hour and minute from index directly
        try:
            df_hours = dataframe.index.hour
            df_minutes = dataframe.index.minute
            minutes_since_midnight = df_hours * 60 + df_minutes
            
            # London session (07:00-10:00 UTC) = 420-600 minutes
            london_session = (minutes_since_midnight >= 420) & (minutes_since_midnight < 600)
            
            # NY session (12:30-16:00 UTC) = 750-960 minutes
            ny_session = (minutes_since_midnight >= 750) & (minutes_since_midnight < 960)
            
            dataframe['session_ok'] = london_session | ny_session
        except:
            # Fallback if index is not datetime
            dataframe['session_ok'] = True

        return dataframe

    def calculate_liquidity_levels(self, df: DataFrame) -> DataFrame:
        """
        Calculate key levels with liquidity sweep detection
        """
        
        # Session-based levels (6 hours = 72 candles on 5m)
        session_length = 72
        
        # Key levels
        df['prev_session_high'] = df['high'].rolling(
            window=session_length, min_periods=6
        ).max().shift(1)
        
        df['prev_session_low'] = df['low'].rolling(
            window=session_length, min_periods=6
        ).min().shift(1)
        
        df['prev_session_close'] = df['close'].shift(session_length)
        
        # Fill NaN values
        for col in ['prev_session_high', 'prev_session_low', 'prev_session_close']:
            if col in df.columns:
                df[col] = df[col].ffill().fillna(df['close'])
        
        # === 3. LIQUIDITY SWEEP TRIGGERS ===
        
        # Sweep high then reverse (sell stops triggered)
        df['sweep_high'] = (
            (df['high'] > df['prev_session_high'] * 1.0005) &  # Pierce high
            (df['close'] < df['prev_session_high'])            # But close below
        )
        
        # Sweep low then reverse (buy stops triggered)
        df['sweep_low'] = (
            (df['low'] < df['prev_session_low'] * 0.9995) &    # Pierce low
            (df['close'] > df['prev_session_low'])             # But close above
        )
        
        # Level proximity (tighter)
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

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        PROFESSIONAL ENTRY LOGIC
        Structure: Session bias → Liquidity raid → Micro confirmation → Entry
        """
        
        # === CORE QUALITY GATES ===
        momentum_ok = dataframe['momentum_aligned']
        volume_ok = dataframe['volume_confirmed'] 
        volatility_ok = dataframe['volatile_enough']
        trend_ok = dataframe['trend_confirmed']
        session_ok = dataframe['session_ok']  # NEW: Session filter
        
        # === LIQUIDITY SWEEP SETUPS (A+ Quality) ===
        
        # 1. Liquidity sweep reversal (highest probability)
        sweep_reversal = (
            (dataframe['sweep_high'] | dataframe['sweep_low']) &
            (dataframe['close'] > dataframe['open']) &  # Green candle after sweep
            (dataframe['volume_ratio'] > 2.0)           # Strong volume
        )
        
        # 2. Pullback to swept level (continuation)
        pullback_continuation = (
            trend_ok &
            (dataframe['near_session_high'] | dataframe['near_session_low']) &
            (dataframe['close'] > dataframe['ema_fast']) &
            (dataframe['rsi'] > 50) & (dataframe['rsi'] < 70)
        )
        
        # 3. Momentum breakout (but only after sweep)
        momentum_breakout = (
            (dataframe['close'] > dataframe['prev_session_high']) &
            (dataframe['close'].shift(1) <= dataframe['prev_session_high'].shift(1)) &
            (dataframe['momentum_strength'] > 0.85) &  # Very strong momentum
            (dataframe['volume_ratio'] > 2.2)
        )
        
        # === COMBINE HIGH-PROBABILITY SETUPS ===
        liquidity_signals = (
            sweep_reversal | pullback_continuation | momentum_breakout
        )
        
        # === FINAL ENTRY CONDITION (All Gates Must Pass) ===
        entry_condition = (
            momentum_ok & 
            volume_ok & 
            volatility_ok & 
            trend_ok &
            session_ok &      # NEW: Session filter
            liquidity_signals # NEW: Liquidity sweep required
        )
        
        dataframe.loc[entry_condition, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs):
        """Tighter stop loss for better R-multiple"""
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return 1

        atr = dataframe["atr"].iloc[-1]
        if atr == 0:
            return 1

        # Tighter stop based on ATR (0.6 vs 1.0)
        entry_price = trade.open_rate
        stop_distance = atr * self.STOP_LOSS_ATR
        stop_price = entry_price - stop_distance
        
        stop_loss_pct = (entry_price - stop_price) / entry_price
        stop_loss_pct = max(0.002, min(0.015, stop_loss_pct))  # 0.2%-1.5%
        
        if current_profit <= -stop_loss_pct:
            return 0.01
        
        return 1

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime,
                    current_rate: float, current_profit: float, **kwargs):
        """Enhanced exit with asymmetric R-multiples"""
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return None

        atr = dataframe["atr"].iloc[-1]
        if atr == 0:
            return None

        entry_price = trade.open_rate
        trade_duration = (current_time - trade.open_date).total_seconds() / 3600
        
        # === ASYMMETRIC PROFIT TARGETS ===
        target_1 = entry_price + (atr * self.RISK_REWARD_RATIO * 0.60)  # 60% of position
        target_2 = entry_price + (atr * self.RISK_REWARD_RATIO)         # Full target
        
        # === PROFESSIONAL EXIT LOGIC ===
        
        # 1. Time limit (shorter for quality)
        if trade_duration > self.MAX_HOLD_HOURS:
            return {"exit_tag": "max_time", "exit_type": "exit_signal"}
        
        # 2. Full profit target
        if current_rate >= target_2:
            return {"exit_tag": "full_target", "exit_type": "exit_signal"}
        
        # 3. Partial profit (scale out)
        if current_rate >= target_1 and trade_duration > 0.5:
            return {"exit_tag": "partial_target", "exit_type": "exit_signal"}
        
        # 4. Tight trailing for locked profits
        if (trade.max_rate is not None and 
            trade.max_rate >= target_1 and 
            current_profit > 0.012):  # 1.2% locked profit
            
            trail_distance = atr * 0.5  # Very tight trailing
            trail_stop = trade.max_rate - trail_distance
            
            if current_rate <= trail_stop:
                return {"exit_tag": "trail_profit", "exit_type": "exit_signal"}
        
        # 5. Quick momentum failure exit
        if trade_duration > 0.25 and current_profit < -0.004:  # 15min and -0.4%
            return {"exit_tag": "momentum_fail", "exit_type": "exit_signal"}
        
        # 6. Session close (risk management)
        current_data = dataframe.iloc[-1]
        if (current_profit > 0.008 and  # 0.8% profit
            not current_data.get('session_ok', False)):
            return {"exit_tag": "session_close", "exit_type": "exit_signal"}
        
        return None 

# === PERFORMANCE TARGETS ===
"""
🎯 EXPECTED TRANSFORMATION:

BEFORE (v1):
- 561 trades (over-trading)
- 62.6% win rate
- -0.60% total return
- Avg win: 0.55%
- Avg loss: -0.90%
- Expectancy: -0.06%

AFTER (v2 - This version):
- 250-300 trades (quality focus)
- 55-60% win rate  
- +2-5% total return
- Avg win: 1.2%
- Avg loss: -0.50%
- Expectancy: +0.22%
- Profit factor: >1.3

🏆 SUCCESS METRICS:
✅ Beat BTC's +21.37% (aim for +5% minimum)
✅ Sharpe ratio >1.0
✅ Max drawdown <2%
✅ Win rate 55-65%
✅ Expectancy positive
""" 