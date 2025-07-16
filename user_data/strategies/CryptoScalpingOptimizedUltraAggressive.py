# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file

"""
Crypto Scalping Ultra-Aggressive v1 - TARGETING 2% MONTHLY RETURNS 🚀
=====================================================================

ULTRA-AGGRESSIVE OPTIMIZATION: Targeting 2% monthly (20 USDT/month)
Current baseline: 3.699 USDT/month validation (18.5% of target)

🔧 ULTRA-AGGRESSIVE CHANGES:
1. MASSIVE ROI TARGETS: 6.0%/4.5%/3.0% (vs 3.0%/2.5%/2.0%)
2. RELAXED MARKET HEALTH: 0.3 (vs 0.5) - Accept more market conditions  
3. RELAXED VOLUME: 1.5x (vs 1.9x) - Lower volume requirements
4. RELAXED RSI: 52 (vs 57) - Earlier entries
5. RELAXED MOMENTUM: 0.65 (vs 0.78) - Accept weaker momentum

🎯 TARGET: Capture larger price moves with more frequent entries
Expected: 2%+ monthly profit with higher risk tolerance
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

class CryptoScalpingOptimizedUltraAggressive(IStrategy):
    """
    ULTRA-AGGRESSIVE SCALPING - Targeting 2% Monthly Returns
    Maximum risk/reward optimization for monthly profit targets
    """

    INTERFACE_VERSION = 3
    timeframe: str = "1m"
    can_short: bool = False
    startup_candle_count: int = 300

    # === ULTRA-AGGRESSIVE ROI LADDER ===
    minimal_roi: Dict[str, float] = {
        "0": 0.060,     # 6.0% immediate (ULTRA-AGGRESSIVE)
        "2": 0.045,     # 4.5% after 2 min (ULTRA-AGGRESSIVE)
        "6": 0.030      # 3.0% after 6 min (ULTRA-AGGRESSIVE)
    }
    
    # === STANDARD STOPLOSS ===
    stoploss: float = -0.025  # Keep same for risk management
    trailing_stop = False
    
    # === ULTRA-RELAXED MARKET HEALTH THRESHOLDS ===
    MIN_MARKET_HEALTH = 0.3      # ULTRA-RELAXED: Accept poor conditions
    MIN_TREND_QUALITY = 0.15     # ULTRA-RELAXED: Accept weak trends 
    MAX_CHOPPINESS = 0.8         # ULTRA-RELAXED: Allow more choppiness
    
    # === ULTRA-RELAXED ENTRY PARAMETERS ===
    MIN_VOLUME_RATIO = 1.5       # ULTRA-RELAXED: Lower volume requirements
    RSI_THRESHOLD = 52           # ULTRA-RELAXED: Earlier entries
    LEVEL_PROXIMITY = 0.005      # Keep same
    MOMENTUM_STRENGTH = 0.65     # ULTRA-RELAXED: Accept weaker momentum
    MIN_ATR_RATIO = 0.002        # ULTRA-RELAXED: Lower volatility requirement

    def informative_pairs(self) -> List[Tuple[str, str]]:
        pairs = []
        if self.dp and self.dp.current_whitelist():
            for pair in self.dp.current_whitelist():
                pairs.append((pair, "15m"))  # Keep 15m for trend context
        return pairs

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Enhanced indicator stack with ultra-relaxed market health awareness"""
        
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
        
        # === ULTRA-RELAXED MARKET HEALTH DETECTION ===
        
        # 1. Ultra-Relaxed Choppiness Index (allow maximum noise)
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
        dataframe['choppy_market'] = dataframe['choppiness'] > (self.MAX_CHOPPINESS * 100)
        
        # 2. Ultra-Relaxed Trend Quality (accept any micro-trend)
        dataframe['ema_alignment'] = (
            (dataframe['ema_fast'] > dataframe['ema_mid']) &
            (dataframe['ema_mid'] > dataframe['ema_slow'])
        ).astype(int)
        
        # Ultra-relaxed trend quality requirements
        dataframe['trend_strength'] = (
            dataframe['ema_alignment'].rolling(3).mean()  # Even shorter period
        )
        dataframe['trend_quality'] = dataframe['trend_strength']
        
        # 3. Ultra-Relaxed Market Health Score (accept almost anything)
        health_factors = [
            (~dataframe['choppy_market']).astype(int),                    # Not too choppy
            (dataframe['trend_quality'] >= self.MIN_TREND_QUALITY).astype(int),  # Minimal trend
            (dataframe['volume_ratio'] > 1.0).astype(int),                # Any volume
            (dataframe['atr'] / dataframe['close'] > 0.001).astype(int)   # Minimal volatility
        ]
        
        dataframe['market_health'] = np.mean(health_factors, axis=0)
        
        # 4. Ultra-relaxed volatility regime
        dataframe['atr_sma'] = dataframe['atr'].rolling(20).mean()
        dataframe['volatility_ratio'] = dataframe['atr'] / dataframe['atr_sma']
        dataframe['favorable_volatility'] = (
            (dataframe['volatility_ratio'] > 1.0) &  # Any increased volatility
            (dataframe['volatility_ratio'] < 3.0)    # Allow very high volatility
        )
        
        # Ultra-relaxed trend strength regime
        dataframe['ema_spread'] = (dataframe['ema_fast'] - dataframe['ema_slow']) / dataframe['close']
        dataframe['trend_strength_alt'] = abs(dataframe['ema_spread'])
        dataframe['trending_regime'] = dataframe['trend_strength_alt'] > 0.001  # Minimal trend requirement
        
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

        # === ULTRA-RELAXED MOMENTUM CALCULATION ===
        momentum_conditions = [
            dataframe["ema_fast"] > dataframe["ema_mid"],
            dataframe["ema_mid"] > dataframe["ema_slow"],
            dataframe["rsi"] > self.RSI_THRESHOLD,  # Ultra-relaxed: 52
            dataframe["macd"] > dataframe["macdsignal"],
            dataframe["close"] > dataframe["ema_fast"]
        ]
        
        # Use np.sum for proper array summation
        momentum_score = np.sum(momentum_conditions, axis=0)
        dataframe['momentum_strength'] = momentum_score / len(momentum_conditions)
        dataframe['momentum_aligned'] = (
            dataframe['momentum_strength'] >= self.MOMENTUM_STRENGTH  # Ultra-relaxed: 0.65
        )
        
        # Ultra-relaxed filters
        dataframe['volume_confirmed'] = (
            dataframe["volume_ratio"] > self.MIN_VOLUME_RATIO  # Ultra-relaxed: 1.5
        )
        
        dataframe['volatile_enough'] = (
            dataframe["atr"] / dataframe["close"] > self.MIN_ATR_RATIO  # Ultra-relaxed: 0.002
        )
        
        # Trend confirmation from 15m
        dataframe['trend_confirmed'] = dataframe.get('trend_15m_15m', True)
        
        # === ULTRA-RELAXED REGIME CONFIRMATION ===
        dataframe['regime_favorable'] = (
            dataframe['favorable_volatility'] &
            dataframe['trending_regime'] &
            (dataframe['market_health'] >= self.MIN_MARKET_HEALTH) &  # Ultra-relaxed: 0.3
            (dataframe['trend_quality'] >= self.MIN_TREND_QUALITY) &  # Ultra-relaxed: 0.15
            (~dataframe['choppy_market'])                             # Ultra-relaxed choppiness
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
        ULTRA-AGGRESSIVE ENTRY LOGIC - Maximum Opportunities for 2% Monthly Target
        """
        
        # === ULTRA-RELAXED QUALITY GATES ===
        momentum_ok = dataframe['momentum_aligned']
        volume_ok = dataframe['volume_confirmed'] 
        volatility_ok = dataframe['volatile_enough']
        trend_ok = dataframe['trend_confirmed']
        session_ok = dataframe['session_ok']
        regime_ok = dataframe['regime_favorable']  # Uses ultra-relaxed market health (0.3)
        
        # === ULTRA-AGGRESSIVE ADAPTIVE FILTERING ===
        # Minimal adaptive filtering (maximum opportunities)
        market_health = dataframe['market_health']
        
        # Ultra-relaxed adaptive volume threshold
        adaptive_volume_threshold = np.where(
            market_health >= 0.4,               # Low threshold
            self.MIN_VOLUME_RATIO,             # Normal volume in decent health
            self.MIN_VOLUME_RATIO * 1.1        # Minimal penalty
        )
        volume_adaptive = dataframe['volume_ratio'] > adaptive_volume_threshold
        
        # Ultra-relaxed adaptive momentum threshold  
        adaptive_momentum_threshold = np.where(
            market_health >= 0.4,               # Low threshold
            self.MOMENTUM_STRENGTH,            # Normal momentum in decent health
            self.MOMENTUM_STRENGTH + 0.05      # Minimal penalty
        )
        momentum_adaptive = dataframe['momentum_strength'] > adaptive_momentum_threshold
        
        # === ULTRA-AGGRESSIVE SETUPS ===
        
        # 1. Ultra-Aggressive Liquidity Sweep (maximum opportunities)
        sweep_reversal_ultra = (
            (dataframe['sweep_high'] | dataframe['sweep_low']) &
            (dataframe['close'] > dataframe['open']) &  # Green candle after sweep
            volume_adaptive &                           # Ultra-relaxed adaptive volume
            momentum_adaptive &                         # Ultra-relaxed adaptive momentum  
            (dataframe['rsi'] > 50) & (dataframe['rsi'] < 90) &  # Ultra-wide RSI range
            (market_health >= 0.2)                     # Ultra-low health requirement
        )
        
        # 2. Ultra-Aggressive Momentum Breakout
        momentum_breakout_ultra = (
            (dataframe['close'] > dataframe['prev_session_high']) &
            (dataframe['close'].shift(1) <= dataframe['prev_session_high'].shift(1)) &
            momentum_adaptive &                         # Ultra-relaxed adaptive momentum
            volume_adaptive &                           # Ultra-relaxed adaptive volume
            (dataframe['rsi'] > 50) & (dataframe['rsi'] < 90) &  # Ultra-wide RSI range
            (dataframe['close'] > dataframe['prev_session_close'] * 1.002) &  # Minimal move requirement
            (market_health >= 0.15)                    # Ultra-low health requirement
        )
        
        # 3. Ultra-Aggressive Session Momentum 
        basic_session_momentum_ultra = (
            session_ok &
            momentum_adaptive &                         # Ultra-relaxed adaptive momentum
            (dataframe['close'] > dataframe['prev_session_close'] * 1.002) &  # Minimal move
            volume_adaptive &                           # Ultra-relaxed adaptive volume
            (dataframe['close'] > dataframe['open']) &  # Green candle
            (dataframe['rsi'] > 50) & (dataframe['rsi'] < 85) &  # Ultra-wide RSI range
            (dataframe['close'] > dataframe['ema_fast'] * 1.001) &  # Minimal EMA requirement
            (market_health >= 0.15)                    # Ultra-low health requirement
        )
        
        # === COMBINE ULTRA-AGGRESSIVE SETUPS ===
        ultra_aggressive_setups = (
            sweep_reversal_ultra | momentum_breakout_ultra | basic_session_momentum_ultra
        )
        
        # === FINAL ENTRY CONDITION WITH ULTRA-RELAXED FILTERING ===
        ultra_aggressive_entry = (
            momentum_ok & 
            volume_ok & 
            volatility_ok & 
            trend_ok &
            regime_ok &                # Uses ultra-relaxed market health (0.3)
            ultra_aggressive_setups &  # Ultra-aggressive setups
            (~dataframe['choppy_market'])  # Ultra-relaxed choppiness filter
        )
        
        dataframe.loc[ultra_aggressive_entry, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        ULTRA-AGGRESSIVE ROI-ONLY STRATEGY: Let ultra-aggressive ROI ladder handle exits
        """
        return dataframe 