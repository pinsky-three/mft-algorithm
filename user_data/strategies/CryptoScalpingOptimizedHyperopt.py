# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file

"""
Crypto Scalping Optimized v12 - 1M TIMEFRAME OPTIMIZATION 🚀
============================================================

PROBLEM IDENTIFIED: v11 Market Health filters too restrictive for 1m
- 1m performance: 1.08% (95 trades) vs 5m: 1.67% (172 trades)
- Over-filtering reducing opportunities by 45%
- Market health requirements too high for micro-timeframe scalping

🔧 1M OPTIMIZATION FIXES:
1. RELAXED MARKET HEALTH: 0.4 vs 0.6 (accept more market conditions)
2. REDUCED CHOPPINESS SENSITIVITY: 0.8 vs 0.6 (allow 1m noise)
3. LOWER TREND QUALITY: 0.15 vs 0.3 (accept micro-trends)
4. ADAPTIVE SCALING: Reduce adaptive thresholds by 50%
5. PAIR OPTIMIZATION: Enhance ETH performance (showed 76.5% win rate)

🎯 TARGET: Increase 1m trades from 95 to 130+ while maintaining quality
Expected: 1.5%+ profit with better opportunity capture
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
    Default values match the proven CryptoScalpingOptimized strategy.
    """

    INTERFACE_VERSION = 3
    timeframe: str = "1m"
    can_short: bool = False
    startup_candle_count: int = 300

    # === HYPEROPT-ENABLED PARAMETERS ===
    # All default values are set to the exact values from the original strategy
    # to ensure identical baseline performance.

    # ROI Table
    roi_0 = DecimalParameter(0.020, 0.035, default=0.025, space="roi", optimize=True)
    roi_2 = DecimalParameter(0.015, 0.028, default=0.020, space="roi", optimize=True)
    roi_6 = DecimalParameter(0.010, 0.020, default=0.015, space="roi", optimize=True)

    # Stoploss
    stoploss_param = DecimalParameter(-0.035, -0.020, default=-0.025, space="stoploss", optimize=True)

    # Market Health (Wider search space)
    MIN_MARKET_HEALTH = DecimalParameter(0.3, 0.7, default=0.5, space="buy", optimize=True)
    MIN_TREND_QUALITY = DecimalParameter(0.1, 0.4, default=0.2, space="buy", optimize=True)
    MAX_CHOPPINESS = DecimalParameter(0.5, 0.9, default=0.7, space="buy", optimize=True)

    # Entry Quality (Wider search space)
    MIN_VOLUME_RATIO = DecimalParameter(1.5, 2.5, default=1.9, space="buy", optimize=True)
    RSI_THRESHOLD = IntParameter(45, 65, default=57, space="buy", optimize=True)
    entry_rsi_threshold = IntParameter(50, 70, default=58, space="buy", optimize=True) # Specific for entry setups
    MOMENTUM_STRENGTH = DecimalParameter(0.6, 0.9, default=0.78, space="buy", optimize=True)
    MIN_ATR_RATIO = DecimalParameter(0.0015, 0.0030, default=0.0022, space="buy", optimize=True)
    
    # Level Proximity
    LEVEL_PROXIMITY = DecimalParameter(0.003, 0.007, default=0.005, space="buy", optimize=True)
    
    # Feature Toggles
    enable_session_filter = BooleanParameter(default=True, space="buy", optimize=True)
    enable_eth_enhancement = BooleanParameter(default=True, space="buy", optimize=True)
    enable_sol_tightening = BooleanParameter(default=True, space="buy", optimize=True)

    # === STRATEGY DEFAULTS (matched to original) ===
    minimal_roi = {
        "0": 0.025
    }
    trailing_stop = False
    
    # Process only new candles
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
                pairs.append((pair, "15m"))
        return pairs

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        
        # === Core Momentum Stack ===
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=10)
        dataframe["ema_mid"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=42)
        
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        macd = ta.MACD(dataframe, fastperiod=12, slowperiod=26, signalperiod=9)
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]
        dataframe["macdhist"] = macd["macdhist"]
        
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["volume_sma"] = ta.SMA(dataframe['volume'], timeperiod=20)
        dataframe["volume_ratio"] = dataframe['volume'] / dataframe["volume_sma"]
        
        # === Market Health Detection ===
        def choppiness_index(df, period=14):
            high_low = df['high'] - df['low']
            high_close = (df['high'] - df['close'].shift(1)).abs()
            low_close = (df['low'] - df['close'].shift(1)).abs()
            true_range = pd.DataFrame([high_low, high_close, low_close]).max()
            atr = true_range.rolling(window=period, min_periods=1).mean()
            high_low_range = df['high'].rolling(window=period, min_periods=1).max() - df['low'].rolling(window=period, min_periods=1).min()
            atr_sum = atr.rolling(window=period, min_periods=1).sum()
            ci = 100 * np.log10(atr_sum / high_low_range) / np.log10(period)
            return ci.fillna(50)
        
        dataframe['choppiness'] = choppiness_index(dataframe)
        dataframe['choppy_market'] = dataframe['choppiness'] > (self.MAX_CHOPPINESS.value * 100)
        
        dataframe['ema_alignment'] = ((dataframe['ema_fast'] > dataframe['ema_mid']) & (dataframe['ema_mid'] > dataframe['ema_slow'])).astype(int)
        dataframe['trend_strength'] = dataframe['ema_alignment'].rolling(5).mean()
        dataframe['trend_quality'] = dataframe['trend_strength']
        
        health_factors = [
            (~dataframe['choppy_market']).astype(int),
            (dataframe['trend_quality'] >= self.MIN_TREND_QUALITY.value).astype(int),
            (dataframe['volume_ratio'] > 1.2).astype(int),
            (dataframe['atr'] / dataframe['close'] > 0.0015).astype(int)
        ]
        dataframe['market_health'] = np.mean(health_factors, axis=0)
        
        dataframe['atr_sma'] = dataframe['atr'].rolling(20).mean()
        dataframe['volatility_ratio'] = dataframe['atr'] / dataframe['atr_sma']
        dataframe['favorable_volatility'] = (dataframe['volatility_ratio'] > 1.1) & (dataframe['volatility_ratio'] < 2.5)
        
        dataframe['ema_spread'] = (dataframe['ema_fast'] - dataframe['ema_slow']) / dataframe['close']
        dataframe['trend_strength_alt'] = abs(dataframe['ema_spread'])
        dataframe['trending_regime'] = dataframe['trend_strength_alt'] > 0.002
        
        dataframe = self.calculate_liquidity_levels(dataframe)
        
        if self.dp and metadata:
            try:
                informative_15m = self.dp.get_pair_dataframe(pair=metadata["pair"], timeframe="15m")
                informative_15m['ema_trend'] = ta.EMA(informative_15m, timeperiod=21)
                informative_15m['trend_15m'] = informative_15m['close'] > informative_15m['ema_trend']
                dataframe = merge_informative_pair(dataframe, informative_15m, self.timeframe, "15m", ffill=True)
            except Exception:
                dataframe['trend_15m_15m'] = True
        else:
            dataframe['trend_15m_15m'] = True

        momentum_conditions = [
            dataframe["ema_fast"] > dataframe["ema_mid"],
            dataframe["ema_mid"] > dataframe["ema_slow"],
            dataframe["rsi"] > self.RSI_THRESHOLD.value,
            dataframe["macd"] > dataframe["macdsignal"],
            dataframe["close"] > dataframe["ema_fast"]
        ]
        momentum_score = np.sum(momentum_conditions, axis=0)
        dataframe['momentum_strength'] = momentum_score / len(momentum_conditions)
        dataframe['momentum_aligned'] = dataframe['momentum_strength'] >= self.MOMENTUM_STRENGTH.value
        
        dataframe['volume_confirmed'] = dataframe["volume_ratio"] > self.MIN_VOLUME_RATIO.value
        dataframe['volatile_enough'] = (dataframe["atr"] / dataframe["close"]) > self.MIN_ATR_RATIO.value
        dataframe['trend_confirmed'] = dataframe.get('trend_15m_15m', True)
        
        dataframe['regime_favorable'] = (
            dataframe['favorable_volatility'] &
            dataframe['trending_regime'] &
            (dataframe['market_health'] >= self.MIN_MARKET_HEALTH.value) &
            (dataframe['trend_quality'] >= self.MIN_TREND_QUALITY.value) &
            (~dataframe['choppy_market'])
        )
        
        if self.enable_session_filter.value:
            try:
                df_hours = dataframe.index.hour
                df_minutes = dataframe.index.minute
                minutes_since_midnight = df_hours * 60 + df_minutes
                london_session = (minutes_since_midnight >= 420) & (minutes_since_midnight < 600)
                ny_session = (minutes_since_midnight >= 750) & (minutes_since_midnight < 960)
                dataframe['session_ok'] = london_session | ny_session
            except:
                dataframe['session_ok'] = True
        else:
            dataframe['session_ok'] = True

        return dataframe

    def calculate_liquidity_levels(self, df: DataFrame) -> DataFrame:
        session_length = 72
        df['prev_session_high'] = df['high'].rolling(window=session_length, min_periods=6).max().shift(1)
        df['prev_session_low'] = df['low'].rolling(window=session_length, min_periods=6).min().shift(1)
        df['prev_session_close'] = df['close'].shift(session_length)
        
        for col in ['prev_session_high', 'prev_session_low', 'prev_session_close']:
            if col in df.columns:
                df[col] = df[col].ffill().fillna(df['close'])
        
        df['sweep_high'] = (df['high'] > df['prev_session_high'] * 1.0005) & (df['close'] < df['prev_session_high'])
        df['sweep_low'] = (df['low'] < df['prev_session_low'] * 0.9995) & (df['close'] > df['prev_session_low'])
        
        df['near_session_high'] = abs(df['close'] - df['prev_session_high']) / df['prev_session_high'] < self.LEVEL_PROXIMITY.value
        df['near_session_low'] = abs(df['close'] - df['prev_session_low']) / df['prev_session_low'] < self.LEVEL_PROXIMITY.value
        df['near_session_close'] = abs(df['close'] - df['prev_session_close']) / df['prev_session_close'] < self.LEVEL_PROXIMITY.value
        
        return df

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        momentum_ok = dataframe['momentum_aligned']
        volume_ok = dataframe['volume_confirmed'] 
        volatility_ok = dataframe['volatile_enough']
        trend_ok = dataframe['trend_confirmed']
        session_ok = dataframe['session_ok']
        regime_ok = dataframe['regime_favorable']
        
        market_health = dataframe['market_health']
        
        adaptive_volume_threshold = np.where(
            market_health >= 0.6,
            self.MIN_VOLUME_RATIO.value,
            self.MIN_VOLUME_RATIO.value * 1.2
        )
        volume_adaptive = dataframe['volume_ratio'] > adaptive_volume_threshold
        
        adaptive_momentum_threshold = np.where(
            market_health >= 0.6,
            self.MOMENTUM_STRENGTH.value,
            self.MOMENTUM_STRENGTH.value + 0.07
        )
        momentum_adaptive = dataframe['momentum_strength'] > adaptive_momentum_threshold
        
        sweep_reversal_1m = (
            (dataframe['sweep_high'] | dataframe['sweep_low']) &
            (dataframe['close'] > dataframe['open']) &
            volume_adaptive &
            momentum_adaptive &
            (dataframe['rsi'] > self.entry_rsi_threshold.value) & (dataframe['rsi'] < 85) &
            (market_health >= 0.5)
        )
        
        momentum_breakout_1m = (
            (dataframe['close'] > dataframe['prev_session_high']) &
            (dataframe['close'].shift(1) <= dataframe['prev_session_high'].shift(1)) &
            momentum_adaptive &
            volume_adaptive &
            (dataframe['rsi'] > self.entry_rsi_threshold.value) & (dataframe['rsi'] < 85) &
            (dataframe['close'] > dataframe['prev_session_close'] * 1.005) &
            (market_health >= 0.45)
        )
        
        basic_session_momentum = (
            session_ok &
            momentum_adaptive &
            (dataframe['close'] > dataframe['prev_session_close'] * 1.004) &
            volume_adaptive &
            (dataframe['close'] > dataframe['open']) &
            (dataframe['rsi'] > self.entry_rsi_threshold.value) & (dataframe['rsi'] < 80) &
            (dataframe['close'] > dataframe['ema_fast'] * 1.0015) &
            (market_health >= 0.4)
        )
        
        balanced_1m_setups = (
            sweep_reversal_1m | momentum_breakout_1m | basic_session_momentum
        )
        
        if metadata and 'pair' in metadata and self.enable_eth_enhancement.value and 'ETH' in metadata['pair']:
            eth_enhanced_momentum = (
                momentum_ok & 
                volume_ok & 
                (dataframe['close'] > dataframe['open']) &
                (dataframe['rsi'] > 55) & (dataframe['rsi'] < 80) &
                (dataframe['close'] > dataframe['ema_fast']) &
                (market_health >= 0.35)
            )
            balanced_1m_setups = balanced_1m_setups | eth_enhanced_momentum
        
        if metadata and 'pair' in metadata and self.enable_sol_tightening.value and 'SOL' in metadata['pair']:
            sol_precise_momentum = (
                momentum_ok & 
                volume_adaptive &
                volatility_ok &
                (dataframe['close'] > dataframe['open']) &
                (dataframe['rsi'] > 62) & (dataframe['rsi'] < 78) &
                (dataframe['close'] > dataframe['ema_fast'] * 1.003) &
                (market_health >= 0.55)
            )
            balanced_1m_setups = balanced_1m_setups | sol_precise_momentum
        
        balanced_1m_entry = (
            momentum_ok & 
            volume_ok & 
            volatility_ok & 
            trend_ok &
            regime_ok &
            balanced_1m_setups &
            (~dataframe['choppy_market'])
        )
        
        dataframe.loc[balanced_1m_entry, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe 