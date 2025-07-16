# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file

"""
Crypto Scalping Optimized v12 - 1M TIMEFRAME OPTIMIZATION 🚀
============================================================

HYPEROPT-ENABLED VERSION - EXACT BASELINE MATCH
Default values and logic IDENTICAL to CryptoScalpingOptimized strategy.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
from pandas import DataFrame

import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy, merge_informative_pair, DecimalParameter, IntParameter, BooleanParameter

class CryptoScalpingOptimizedHyperopt(IStrategy):
    """
    1M-OPTIMIZED SCALPING - HYPEROPT-ENABLED
    Default values match the proven CryptoScalpingOptimized strategy EXACTLY.
    """

    INTERFACE_VERSION = 3
    timeframe: str = "1m"
    can_short: bool = False
    startup_candle_count: int = 300

    # === HYPEROPT-ENABLED PARAMETERS ===
    # All default values are set to the exact values from the original strategy

    # ROI Table
    roi_0 = DecimalParameter(0.020, 0.035, default=0.025, space="roi", optimize=True)
    roi_2 = DecimalParameter(0.015, 0.028, default=0.020, space="roi", optimize=True)
    roi_6 = DecimalParameter(0.010, 0.020, default=0.015, space="roi", optimize=True)

    # Stoploss
    stoploss_param = DecimalParameter(-0.035, -0.020, default=-0.025, space="stoploss", optimize=True)

    # Market Health
    MIN_MARKET_HEALTH = DecimalParameter(0.3, 0.7, default=0.5, space="buy", optimize=True)
    MIN_TREND_QUALITY = DecimalParameter(0.1, 0.4, default=0.2, space="buy", optimize=True)
    MAX_CHOPPINESS = DecimalParameter(0.5, 0.9, default=0.7, space="buy", optimize=True)

    # Entry Quality
    MIN_VOLUME_RATIO = DecimalParameter(1.5, 2.5, default=1.9, space="buy", optimize=True)
    RSI_THRESHOLD = IntParameter(45, 65, default=57, space="buy", optimize=True)
    MOMENTUM_STRENGTH = DecimalParameter(0.6, 0.9, default=0.78, space="buy", optimize=True)
    MIN_ATR_RATIO = DecimalParameter(0.0015, 0.0030, default=0.0022, space="buy", optimize=True)
    
    # Level Proximity
    LEVEL_PROXIMITY = DecimalParameter(0.003, 0.007, default=0.005, space="buy", optimize=True)

    # === STRATEGY DEFAULTS (matched to original) ===
    minimal_roi = {
        "0": 0.025
    }
    trailing_stop = False
    process_only_new_candles = True

    def __init__(self, config: dict):
        super().__init__(config)
        self.stoploss = self.stoploss_param.value
        self.minimal_roi = {
            "0": self.roi_0.value,
            "2": self.roi_2.value,
            "6": self.roi_6.value,
        }

    def informative_pairs(self) -> List[Tuple[str, str]]:
        pairs = []
        if self.dp and self.dp.current_whitelist():
            for pair in self.dp.current_whitelist():
                pairs.append((pair, "15m"))  # Keep 15m for trend context
        return pairs

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Enhanced indicator stack with 1m-optimized market health awareness"""
        
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
        
        # === 1M-OPTIMIZED MARKET HEALTH DETECTION ===
        
        # 1. Relaxed Choppiness Index (allow more 1m noise)
        def choppiness_index(df, period=14):
            """Calculate Choppiness Index - higher values = more choppy/ranging"""
            # Calculate True Range
            high_low = df['high'] - df['low']
            high_close = (df['high'] - df['close'].shift(1)).abs()
            low_close = (df['low'] - df['close'].shift(1)).abs()
            true_range = pd.DataFrame([high_low, high_close, low_close]).max()
            
            # Calculate ATR manually using pandas
            atr = true_range.rolling(window=period, min_periods=1).mean()
            
            # Calculate high-low range over period
            high_low_range = df['high'].rolling(period).max() - df['low'].rolling(period).min()
            
            # Calculate Choppiness Index
            atr_sum = atr.rolling(period).sum()
            ci = 100 * np.log10(atr_sum / high_low_range) / np.log10(period)
            return ci.fillna(50)  # Default to neutral
        
        dataframe['choppiness'] = choppiness_index(dataframe)
        dataframe['choppy_market'] = dataframe['choppiness'] > (self.MAX_CHOPPINESS.value * 100)
        
        # 2. Relaxed Trend Quality (accept micro-trends)
        dataframe['ema_alignment'] = (
            (dataframe['ema_fast'] > dataframe['ema_mid']) &
            (dataframe['ema_mid'] > dataframe['ema_slow'])
        ).astype(int)
        
        # Reduce trend quality requirements for 1m
        dataframe['trend_strength'] = (
            dataframe['ema_alignment'].rolling(5).mean()  # Shorter period for 1m
        )
        dataframe['trend_quality'] = dataframe['trend_strength']
        
        # 3. 1m-Optimized Market Health Score (more lenient)
        health_factors = [
            (~dataframe['choppy_market']).astype(int),                    # Not choppy
            (dataframe['trend_quality'] >= self.MIN_TREND_QUALITY.value).astype(int),  # Micro-trend OK
            (dataframe['volume_ratio'] > 1.2).astype(int),                # Basic volume
            (dataframe['atr'] / dataframe['close'] > 0.0015).astype(int)   # Minimal volatility
        ]
        
        dataframe['market_health'] = np.mean(health_factors, axis=0)
        
        # 4. Volatility regime (1m-optimized)
        dataframe['atr_sma'] = dataframe['atr'].rolling(20).mean()
        dataframe['volatility_ratio'] = dataframe['atr'] / dataframe['atr_sma']
        dataframe['favorable_volatility'] = (
            (dataframe['volatility_ratio'] > 1.1) &  # Reduced from 1.2
            (dataframe['volatility_ratio'] < 2.5)    # Allow higher volatility
        )
        
        # Trend strength regime (1m-optimized)
        dataframe['ema_spread'] = (dataframe['ema_fast'] - dataframe['ema_slow']) / dataframe['close']
        dataframe['trend_strength_alt'] = abs(dataframe['ema_spread'])
        dataframe['trending_regime'] = dataframe['trend_strength_alt'] > 0.002  # Reduced from 0.003
        
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
        else:
            # Fallback if no dataProvider or metadata
            dataframe['trend_15m_15m'] = True

        # === 1M-OPTIMIZED MOMENTUM CALCULATION ===
        momentum_conditions = [
            dataframe["ema_fast"] > dataframe["ema_mid"],
            dataframe["ema_mid"] > dataframe["ema_slow"],
            dataframe["rsi"] > self.RSI_THRESHOLD.value,  # Reduced from 60 to 55
            dataframe["macd"] > dataframe["macdsignal"],
            dataframe["close"] > dataframe["ema_fast"]
        ]
        
        # Use np.sum for proper array summation
        momentum_score = np.sum(momentum_conditions, axis=0)
        dataframe['momentum_strength'] = momentum_score / len(momentum_conditions)
        dataframe['momentum_aligned'] = (
            dataframe['momentum_strength'] >= self.MOMENTUM_STRENGTH.value  # Reduced from 0.80 to 0.75
        )
        
        # 1m-optimized filters (more lenient)
        dataframe['volume_confirmed'] = (
            dataframe["volume_ratio"] > self.MIN_VOLUME_RATIO.value  # Reduced from 2.0 to 1.8
        )
        
        dataframe['volatile_enough'] = (
            dataframe["atr"] / dataframe["close"] > self.MIN_ATR_RATIO.value  # Reduced from 0.0025 to 0.002
        )
        
        # Trend confirmation from 15m
        dataframe['trend_confirmed'] = dataframe.get('trend_15m_15m', True)
        
        # === 1M-OPTIMIZED REGIME CONFIRMATION ===
        dataframe['regime_favorable'] = (
            dataframe['favorable_volatility'] &
            dataframe['trending_regime'] &
            (dataframe['market_health'] >= self.MIN_MARKET_HEALTH.value) &  # Relaxed from 0.6 to 0.4
            (dataframe['trend_quality'] >= self.MIN_TREND_QUALITY.value) &  # Relaxed from 0.3 to 0.15
            (~dataframe['choppy_market'])                             # Relaxed choppiness threshold
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
            abs(df['close'] - df['prev_session_high']) / df['prev_session_high'] < self.LEVEL_PROXIMITY.value
        )
        df['near_session_low'] = (
            abs(df['close'] - df['prev_session_low']) / df['prev_session_low'] < self.LEVEL_PROXIMITY.value
        )
        df['near_session_close'] = (
            abs(df['close'] - df['prev_session_close']) / df['prev_session_close'] < self.LEVEL_PROXIMITY.value
        )
        
        return df

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        1M-OPTIMIZED ENTRY LOGIC - Relaxed Market Health for Better Opportunities
        Reduced over-filtering while maintaining quality
        """
        
        # === RELAXED QUALITY GATES FOR 1M ===
        momentum_ok = dataframe['momentum_aligned']
        volume_ok = dataframe['volume_confirmed'] 
        volatility_ok = dataframe['volatile_enough']
        trend_ok = dataframe['trend_confirmed']
        session_ok = dataframe['session_ok']
        regime_ok = dataframe['regime_favorable']  # Now uses relaxed market health (0.4)
        
        # === BALANCED ADAPTIVE FILTERING FOR 1M ===
        # Moderate adaptive filtering (balanced approach)
        market_health = dataframe['market_health']
        
        # Balanced adaptive volume threshold
        adaptive_volume_threshold = np.where(
            market_health >= 0.6,               # Moderate threshold
            self.MIN_VOLUME_RATIO.value,             # Normal volume in good health
            self.MIN_VOLUME_RATIO.value * 1.2        # Moderate penalty
        )
        volume_adaptive = dataframe['volume_ratio'] > adaptive_volume_threshold
        
        # Balanced adaptive momentum threshold  
        adaptive_momentum_threshold = np.where(
            market_health >= 0.6,               # Moderate threshold
            self.MOMENTUM_STRENGTH.value,            # Normal momentum in good health
            self.MOMENTUM_STRENGTH.value + 0.07      # Moderate penalty
        )
        momentum_adaptive = dataframe['momentum_strength'] > adaptive_momentum_threshold
        
        # === BALANCED 1M SETUPS WITH MODERATE REQUIREMENTS ===
        
        # 1. Balanced Liquidity Sweep (quality focused)
        sweep_reversal_1m = (
            (dataframe['sweep_high'] | dataframe['sweep_low']) &
            (dataframe['close'] > dataframe['open']) &  # Green candle after sweep
            volume_adaptive &                           # Balanced adaptive volume
            momentum_adaptive &                         # Balanced adaptive momentum  
            (dataframe['rsi'] > 58) & (dataframe['rsi'] < 85) &  # Moderate RSI requirement
            (market_health >= 0.5)                     # Balanced health requirement
        )
        
        # 2. 1m Momentum Breakout (balanced)
        momentum_breakout_1m = (
            (dataframe['close'] > dataframe['prev_session_high']) &
            (dataframe['close'].shift(1) <= dataframe['prev_session_high'].shift(1)) &
            momentum_adaptive &                         # Balanced adaptive momentum
            volume_adaptive &                           # Balanced adaptive volume
            (dataframe['rsi'] > 58) & (dataframe['rsi'] < 85) &  # Moderate RSI requirement
            (dataframe['close'] > dataframe['prev_session_close'] * 1.005) &  # Moderate move requirement
            (market_health >= 0.45)                    # Moderate health requirement
        )
        
        # 3. Balanced 1m Session Momentum 
        basic_session_momentum = (
            session_ok &
            momentum_adaptive &                         # Balanced adaptive momentum
            (dataframe['close'] > dataframe['prev_session_close'] * 1.004) &  # Moderate move
            volume_adaptive &                           # Balanced adaptive volume
            (dataframe['close'] > dataframe['open']) &  # Green candle
            (dataframe['rsi'] > 58) & (dataframe['rsi'] < 80) &  # Moderate RSI requirement
            (dataframe['close'] > dataframe['ema_fast'] * 1.0015) &  # Moderate momentum
            (market_health >= 0.4)                     # Moderate health requirement
        )
        
        # Combine all balanced 1m setups
        balanced_1m_setups = (
            sweep_reversal_1m | momentum_breakout_1m | basic_session_momentum
        )
        
        # === BALANCED PAIR-SPECIFIC OPTIMIZATIONS FOR 1M ===
        # ETH/USDT showed 76.5% win rate on 1m - enhance moderately
        if metadata and 'pair' in metadata:
            pair = metadata['pair']
            
            # ETH-specific enhancements (moderate approach)
            if 'ETH' in pair:
                eth_enhanced_momentum = (
                    momentum_ok & 
                    volume_ok & 
                    (dataframe['close'] > dataframe['open']) &  # Green candle
                    (dataframe['rsi'] > 55) & (dataframe['rsi'] < 80) &  # Moderate RSI for ETH
                    (dataframe['close'] > dataframe['ema_fast']) &
                    (market_health >= 0.35)  # Moderate relaxation for ETH
                )
                balanced_1m_setups = balanced_1m_setups | eth_enhanced_momentum
            
            # SOL-specific adjustments (tighter controls due to underperformance)
            elif 'SOL' in pair:
                sol_precise_momentum = (
                    momentum_ok & 
                    volume_adaptive &  # Use adaptive for SOL
                    volatility_ok &
                    (dataframe['close'] > dataframe['open']) &  # Green candle
                    (dataframe['rsi'] > 62) & (dataframe['rsi'] < 78) &  # Tighter RSI for SOL
                    (dataframe['close'] > dataframe['ema_fast'] * 1.003) &  # Stronger momentum required
                    (market_health >= 0.55)  # Higher health requirement for SOL
                )
                balanced_1m_setups = balanced_1m_setups | sol_precise_momentum
        
        # === FINAL ENTRY CONDITION WITH BALANCED FILTERING ===
        balanced_1m_entry = (
            momentum_ok & 
            volume_ok & 
            volatility_ok & 
            trend_ok &
            regime_ok &                # Uses balanced market health (0.5)
            balanced_1m_setups &       # Balanced 1m setups (includes pair-specific)
            (~dataframe['choppy_market'])  # Avoid choppy conditions
        )
        
        dataframe.loc[balanced_1m_entry, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Exit handled by ROI/stoploss - no additional exit signals for 1m
        """
        return dataframe 