# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file

"""
Crypto Scalping Optimized v6 - ROI-ONLY SIMPLIFICATION 🎯
========================================================

BACK TO BASICS: ROI exits work perfectly, custom exits destroy profitability!

📊 ANALYSIS OF COMPLEX v5:
- ROI exits: 14 trades, 100% win rate, +1.67% profit ✅
- Custom exits: 656 trades, 40.7% win rate, -5.13% loss ❌
- Total result: -3.47% return ❌

🎯 SIMPLIFICATION STRATEGY:
- Remove ALL custom exit logic
- Keep only ROI ladder + stoploss
- Let profitable ROI exits do their job
- Stop over-engineering exits

💡 HYPOTHESIS: Sometimes simpler is better!
100% win rate ROI exits suggest the entry logic + ROI ladder is solid.
Custom exits are the problem, not the solution.

🏆 MISSION: ACHIEVE PROFITABILITY THROUGH SIMPLIFICATION!
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
    ROI-ONLY SIMPLIFICATION: Let profitable ROI exits do their job!
    Entry logic + ROI ladder = 100% win rate on ROI exits
    Remove all custom exit complexity that destroys profitability
    """

    INTERFACE_VERSION = 3
    timeframe: str = "5m"
    can_short: bool = False
    startup_candle_count: int = 300

    # === PROFITABLE ROI LADDER (Only Exit Logic) ===
    minimal_roi: Dict[str, float] = {
        "0": 0.012,     # 1.2% immediate
        "30": 0.008,    # 0.8% after 30 min
        "120": 0.004    # 0.4% after 2h
    }
    
    # === SIMPLE STOPLOSS (Risk Management Only) ===
    stoploss: float = -0.08  # 8% maximum loss
    trailing_stop = False
    
    # === ENTRY PARAMETERS (Keep Working Logic) ===
    MIN_VOLUME_RATIO = 1.5
    RSI_THRESHOLD = 48
    LEVEL_PROXIMITY = 0.012
    MOMENTUM_STRENGTH = 0.65
    MIN_ATR_RATIO = 0.0015

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
        GOLDILOCKS ENTRY LOGIC - Perfectly Balanced
        Multiple high-probability paths to profitability
        """
        
        # === CORE QUALITY GATES ===
        momentum_ok = dataframe['momentum_aligned']
        volume_ok = dataframe['volume_confirmed'] 
        volatility_ok = dataframe['volatile_enough']
        trend_ok = dataframe['trend_confirmed']
        session_ok = dataframe['session_ok']
        
        # === PREMIUM SETUPS (A+ Quality) ===
        
        # 1. Liquidity sweep reversal (highest probability)
        sweep_reversal = (
            (dataframe['sweep_high'] | dataframe['sweep_low']) &
            (dataframe['close'] > dataframe['open']) &  # Green candle after sweep
            (dataframe['volume_ratio'] > 1.8)           # Strong volume
        )
        
        # 2. Momentum breakout above key levels
        momentum_breakout = (
            (dataframe['close'] > dataframe['prev_session_high']) &
            (dataframe['close'].shift(1) <= dataframe['prev_session_high'].shift(1)) &
            (dataframe['momentum_strength'] > 0.80) &  # Strong momentum
            (dataframe['volume_ratio'] > 1.8)
        )
        
        # 3. Pullback to key levels (trend continuation)
        pullback_continuation = (
            trend_ok &
            (dataframe['near_session_high'] | dataframe['near_session_low']) &
            (dataframe['close'] > dataframe['ema_fast']) &
            (dataframe['rsi'] > 35) & (dataframe['rsi'] < 70)  # Wider RSI range
        )
        
        # 4. Strong momentum setup (no sweep required)
        momentum_setup = (
            (dataframe['momentum_strength'] > 0.75) &  # Lower threshold
            (dataframe['close'] > dataframe['prev_session_close']) &
            (dataframe['volume_ratio'] > 1.6) &  # Lower volume requirement
            (dataframe['close'] > dataframe['open'])
        )
        
        # 5. Bounce from session low
        bounce_setup = (
            (dataframe['low'] <= dataframe['prev_session_low'] * 1.008) &
            (dataframe['close'] > dataframe['prev_session_low'] * 1.012) &
            (dataframe['close'] > dataframe['open']) &
            (dataframe['rsi'] < 50)  # Less restrictive oversold
        )
        
        # === COMBINE ALL HIGH-PROBABILITY SETUPS ===
        setup_signals = (
            sweep_reversal | momentum_breakout | pullback_continuation | 
            momentum_setup | bounce_setup
        )
        
        # === FINAL ENTRY CONDITION (Quality Gates + Any Setup) ===
        entry_condition = (
            momentum_ok & 
            volume_ok & 
            volatility_ok & 
            trend_ok &
            session_ok &      # Session filter always required
            setup_signals     # Any high-probability setup
        )
        
        dataframe.loc[entry_condition, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        ROI-ONLY STRATEGY: No custom exit signals
        Let ROI ladder handle all exits (100% win rate!)
        """
        return dataframe

# === ROI-ONLY SIMPLIFICATION TARGETS ===
"""
🎯 STRATEGY SIMPLIFICATION FOR PROFITABILITY:

COMPLEX EXIT ANALYSIS:
- Custom exits: 656 trades, 40.7% win rate, -5.13% loss ❌
- ROI exits: 14 trades, 100% win rate, +1.67% profit ✅

ROI-ONLY HYPOTHESIS:
- Entry logic is solid (generates good setups)
- ROI ladder works perfectly (100% win rate)
- Custom exits are over-engineering and harmful
- Simplification = profitability

🏆 EXPECTED RESULTS:
- Higher % of ROI exits (currently only 14/671 = 2.1%)
- 100% win rate maintained on ROI exits
- Elimination of losing custom exits
- Net positive returns from simplified approach

📊 SUCCESS METRICS:
✅ Positive total return (target +1-3%)
✅ Higher % of profitable ROI exits
✅ Elimination of -5.13% custom exit losses
✅ Clean, simple, profitable strategy
✅ Proof that simpler approach works better

🏆 MISSION: PROFITABILITY THROUGH SIMPLIFICATION!
""" 