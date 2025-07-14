# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file

"""
Crypto Scalping Optimized v10 - BALANCED RISK/REWARD FIX 🎯
===========================================================

CRITICAL ISSUES IDENTIFIED FROM 6-MONTH BACKTEST:
- ROI exits: +82.452 USDT (81 trades, 100% win rate, 2.04% avg)
- Stop losses: -84.590 USDT (42 trades, 0% win rate, -4.04% avg) 
- Net result: -2.139 USDT loss (-0.21%)

🔧 OPTIMIZATION FIXES:
1. STOP LOSS: -4% → -2.5% (reduce 1m noise exits)
2. ROI LADDER: 3%/2.5%/2% → 2.5%/2%/1.5% (better balance)
3. FILTERING: Reduce over-restrictive thresholds for more opportunities
4. REGIME FILTER: Add market condition awareness

🎯 TARGET: Positive consistent returns with balanced risk/reward
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
    BALANCED RISK/REWARD SCALPING - Optimized for Consistent Profits
    Fix stop loss bleeding + improve opportunity capture + regime awareness
    """

    INTERFACE_VERSION = 3
    timeframe: str = "1m"
    can_short: bool = False
    startup_candle_count: int = 300

    # === BALANCED ROI LADDER (Better Risk/Reward) ===
    minimal_roi: Dict[str, float] = {
        "0": 0.025,     # 2.5% immediate (vs 3.0% - more realistic)
        "2": 0.020,     # 2.0% after 2 min (vs 2.5% - balanced)
        "6": 0.015      # 1.5% after 6 min (vs 2.0% - conservative)
    }
    
    # === OPTIMIZED STOPLOSS (Reduce 1m Noise) ===
    stoploss: float = -0.025  # 2.5% (vs 4% - reduce false exits)
    trailing_stop = False
    
    # === BALANCED ENTRY PARAMETERS (Less Restrictive) ===
    MIN_VOLUME_RATIO = 2.0       # Strong volume (vs 2.5 - less restrictive)
    RSI_THRESHOLD = 60           # Strong momentum (vs 65 - more opportunities)
    LEVEL_PROXIMITY = 0.005      # Level proximity
    MOMENTUM_STRENGTH = 0.80     # Strong momentum (vs 0.85 - balanced)
    MIN_ATR_RATIO = 0.0025       # Volatility threshold

    def informative_pairs(self) -> List[Tuple[str, str]]:
        pairs = []
        if self.dp and self.dp.current_whitelist():
            for pair in self.dp.current_whitelist():
                pairs.append((pair, "15m"))  # Keep 15m for trend context
        return pairs

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Professional indicator stack with market regime awareness"""
        
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
        
        # === NEW: MARKET REGIME DETECTION ===
        # Volatility regime (for favorable conditions)
        dataframe['atr_sma'] = ta.SMA(dataframe['atr'], timeperiod=20)
        dataframe['volatility_ratio'] = dataframe['atr'] / dataframe['atr_sma']
        dataframe['favorable_volatility'] = (
            (dataframe['volatility_ratio'] > 1.2) &  # Higher than normal vol
            (dataframe['volatility_ratio'] < 2.0)    # But not extreme
        )
        
        # Trend strength regime
        dataframe['ema_spread'] = (dataframe['ema_fast'] - dataframe['ema_slow']) / dataframe['close']
        dataframe['trend_strength'] = abs(dataframe['ema_spread'])
        dataframe['trending_regime'] = dataframe['trend_strength'] > 0.003  # 0.3% minimum trend
        
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

        # === MOMENTUM CALCULATION (Balanced Thresholds) ===
        momentum_conditions = [
            dataframe["ema_fast"] > dataframe["ema_mid"],
            dataframe["ema_mid"] > dataframe["ema_slow"],
            dataframe["rsi"] > self.RSI_THRESHOLD,
            dataframe["macd"] > dataframe["macdsignal"],
            dataframe["close"] > dataframe["ema_fast"]
        ]
        
        # Use np.sum for proper array summation
        momentum_score = np.sum(momentum_conditions, axis=0)
        dataframe['momentum_strength'] = momentum_score / len(momentum_conditions)
        dataframe['momentum_aligned'] = (
            dataframe['momentum_strength'] >= self.MOMENTUM_STRENGTH
        )
        
        # Enhanced filters (less restrictive)
        dataframe['volume_confirmed'] = (
            dataframe["volume_ratio"] > self.MIN_VOLUME_RATIO
        )
        
        dataframe['volatile_enough'] = (
            dataframe["atr"] / dataframe["close"] > self.MIN_ATR_RATIO
        )
        
        # Trend confirmation from 15m
        dataframe['trend_confirmed'] = dataframe.get('trend_15m_15m', True)
        
        # === NEW: REGIME CONFIRMATION ===
        dataframe['regime_favorable'] = (
            dataframe['favorable_volatility'] &
            dataframe['trending_regime']
        )
        
        # === SESSION BIAS FILTER ===
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
        
        # === LIQUIDITY SWEEP TRIGGERS ===
        
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
        BALANCED ENTRY LOGIC - Quality Setups with Better Opportunity Capture
        Reduced over-filtering while maintaining edge quality
        """
        
        # === BALANCED QUALITY GATES ===
        momentum_ok = dataframe['momentum_aligned']
        volume_ok = dataframe['volume_confirmed'] 
        volatility_ok = dataframe['volatile_enough']
        trend_ok = dataframe['trend_confirmed']
        session_ok = dataframe['session_ok']
        regime_ok = dataframe['regime_favorable']  # NEW: Regime filter
        
        # === BALANCED SETUPS (Less Restrictive but Still Quality) ===
        
        # 1. Liquidity sweep reversal (balanced thresholds)
        sweep_reversal = (
            (dataframe['sweep_high'] | dataframe['sweep_low']) &
            (dataframe['close'] > dataframe['open']) &  # Green candle after sweep
            (dataframe['volume_ratio'] > 2.2) &         # Strong volume (vs 3.0)
            (dataframe['momentum_strength'] > 0.85) &   # Strong momentum (vs 0.90)
            (dataframe['rsi'] > 65) & (dataframe['rsi'] < 85)  # Strong but not extreme
        )
        
        # 2. Momentum breakout (quality with opportunities)
        momentum_breakout = (
            (dataframe['close'] > dataframe['prev_session_high']) &
            (dataframe['close'].shift(1) <= dataframe['prev_session_high'].shift(1)) &
            (dataframe['momentum_strength'] > 0.85) &   # Strong momentum (vs 0.90)
            (dataframe['volume_ratio'] > 2.2) &         # Strong volume (vs 2.8)
            (dataframe['rsi'] > 65) &                   # Strong RSI (vs 70)
            (dataframe['rsi'] < 85) &                   # But not overbought
            (dataframe['close'] > dataframe['prev_session_close'] * 1.006)  # Above session (vs 1.008)
        )
        
        # 3. Session momentum (balanced quality)
        session_momentum = (
            session_ok &
            (dataframe['momentum_strength'] > 0.85) &   # Strong momentum (vs 0.90)
            (dataframe['close'] > dataframe['prev_session_close'] * 1.008) &  # Well above session
            (dataframe['volume_ratio'] > 2.5) &         # Strong volume (vs 3.0)
            (dataframe['close'] > dataframe['open']) &  # Green candle
            (dataframe['rsi'] > 60) & (dataframe['rsi'] < 80) &  # Strong RSI range (vs 65)
            (dataframe['close'] > dataframe['ema_fast'] * 1.002)  # Above EMA (vs 1.003)
        )
        
        # === COMBINE BALANCED SETUPS ===
        quality_setups = (
            sweep_reversal | momentum_breakout | session_momentum
        )
        
        # === BALANCED ENTRY CONDITION (All Gates + Quality Setups) ===
        balanced_entry = (
            momentum_ok & 
            volume_ok & 
            volatility_ok & 
            trend_ok &
            session_ok &           # Session filter
            regime_ok &            # NEW: Regime filter for favorable conditions
            quality_setups         # Quality setups with balanced thresholds
        )
        
        dataframe.loc[balanced_entry, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        BALANCED ROI-ONLY STRATEGY: Let optimized ROI ladder handle exits
        """
        return dataframe

# === BALANCED STRATEGY OPTIMIZATION SUMMARY ===
"""
🎯 RISK/REWARD OPTIMIZATION FIXES:

STOP LOSS FIX:
❌ Old: -4% stop loss (too tight for 1m noise)
✅ New: -2.5% stop loss (reduce false exits)

ROI BALANCE:
❌ Old: 3%/2.5%/2% (too aggressive)
✅ New: 2.5%/2%/1.5% (balanced risk/reward)

FILTERING OPTIMIZATION:
❌ Old: Ultra-restrictive (missed opportunities)
✅ New: Balanced quality (more setups, maintained edge)

REGIME AWARENESS:
❌ Old: Blind trading in all conditions
✅ New: Trade only in favorable volatility/trend regimes

🏆 EXPECTED IMPROVEMENT:
- Fewer stop losses from 1m noise
- Better risk/reward balance (1:1 vs 1:2)
- More trading opportunities (balanced filters)
- Higher probability setups (regime awareness)
- Consistent positive returns over longer periods
""" 