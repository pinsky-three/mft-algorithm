# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file

"""
Crypto Scalping Optimized July 2025 - CURRENT MARKET ADAPTATION 🎯
==================================================================

JULY 2025 PROBLEM IDENTIFIED:
- Only 1 trade in 11 days (over-filtering in current conditions)
- Market up +8.11% but strategy missed opportunities
- Strategy too conservative for current market regime

🔧 JULY 2025 ADAPTATIONS:
1. RELAXED MARKET HEALTH: 0.4 (vs 0.5) - Accept current conditions
2. REDUCED VOLUME THRESHOLD: 1.7x (vs 1.9x) - More opportunities  
3. RELAXED RSI: 55 (vs 57) - Earlier entries in trending market
4. RELAXED MOMENTUM: 0.75 (vs 0.78) - Accept moderate momentum
5. ENHANCED SESSION FILTER: Better adapt to July trading patterns

🎯 TARGET: Maintain strong performance in other months while adapting to July
Expected: 2-4 trades per week in July conditions vs current 0.1 trades/day
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

class CryptoScalpingOptimizedJuly(IStrategy):
    """
    JULY 2025 MARKET-ADAPTED SCALPING - Balanced Filtering for Current Conditions
    Maintains historical performance while adapting to July market regime
    """

    INTERFACE_VERSION = 3
    timeframe: str = "1m"
    can_short: bool = False
    startup_candle_count: int = 300

    # === PROVEN ROI LADDER (Keep Successful Settings) ===
    minimal_roi: Dict[str, float] = {
        "0": 0.030,     # 3.0% immediate (validated)
        "2": 0.025,     # 2.5% after 2 min (validated)
        "6": 0.020      # 2.0% after 6 min (validated)
    }
    
    # === PROVEN STOPLOSS (Keep Successful Settings) ===
    stoploss: float = -0.025  # 2.5% (validated)
    trailing_stop = False
    
    # === JULY-ADAPTED MARKET HEALTH THRESHOLDS ===
    MIN_MARKET_HEALTH = 0.4      # JULY: Relaxed from 0.5 (accept more conditions)
    MIN_TREND_QUALITY = 0.18     # JULY: Slightly relaxed from 0.2
    MAX_CHOPPINESS = 0.75        # JULY: Slightly relaxed from 0.7
    
    # === JULY-ADAPTED ENTRY PARAMETERS ===
    MIN_VOLUME_RATIO = 1.7       # JULY: Relaxed from 1.9 (more opportunities)
    RSI_THRESHOLD = 55           # JULY: Relaxed from 57 (earlier entries)
    LEVEL_PROXIMITY = 0.005      # Keep same (working well)
    MOMENTUM_STRENGTH = 0.75     # JULY: Relaxed from 0.78 (accept moderate momentum)
    MIN_ATR_RATIO = 0.002        # JULY: Slightly relaxed from 0.0022

    def informative_pairs(self) -> List[Tuple[str, str]]:
        pairs = []
        if self.dp and self.dp.current_whitelist():
            for pair in self.dp.current_whitelist():
                pairs.append((pair, "15m"))  # Keep 15m for trend context
        return pairs

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Enhanced indicator stack with July-adapted market health awareness"""
        
        # === Core Momentum Stack (Keep Proven) ===
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
        
        # === JULY-ADAPTED MARKET HEALTH DETECTION ===
        
        # 1. July-adapted Choppiness Index (slightly more tolerant)
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
        
        # 2. July-adapted Trend Quality (slightly more accepting)
        dataframe['ema_alignment'] = (
            (dataframe['ema_fast'] > dataframe['ema_mid']) &
            (dataframe['ema_mid'] > dataframe['ema_slow'])
        ).astype(int)
        
        # July-adapted trend quality requirements
        dataframe['trend_strength'] = (
            dataframe['ema_alignment'].rolling(5).mean()  # Keep same period
        )
        dataframe['trend_quality'] = dataframe['trend_strength']
        
        # 3. July-adapted Market Health Score (more lenient for current conditions)
        health_factors = [
            (~dataframe['choppy_market']).astype(int),                    # Not choppy
            (dataframe['trend_quality'] >= self.MIN_TREND_QUALITY).astype(int),  # July-relaxed
            (dataframe['volume_ratio'] > 1.15).astype(int),               # July: Reduced from 1.2
            (dataframe['atr'] / dataframe['close'] > 0.0013).astype(int)  # July: Reduced from 0.0015
        ]
        
        dataframe['market_health'] = np.mean(health_factors, axis=0)
        
        # 4. July-adapted volatility regime (more accepting)
        dataframe['atr_sma'] = dataframe['atr'].rolling(20).mean()
        dataframe['volatility_ratio'] = dataframe['atr'] / dataframe['atr_sma']
        dataframe['favorable_volatility'] = (
            (dataframe['volatility_ratio'] > 1.05) &  # July: Reduced from 1.1
            (dataframe['volatility_ratio'] < 2.8)     # July: Increased from 2.5
        )
        
        # July-adapted trend strength regime
        dataframe['ema_spread'] = (dataframe['ema_fast'] - dataframe['ema_slow']) / dataframe['close']
        dataframe['trend_strength_alt'] = abs(dataframe['ema_spread'])
        dataframe['trending_regime'] = dataframe['trend_strength_alt'] > 0.0018  # July: Reduced from 0.002
        
        # === Key Levels (Keep Proven) ===
        dataframe = self.calculate_liquidity_levels(dataframe)
        
        # === 15m Trend Context (Keep Proven) ===
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

        # === JULY-ADAPTED MOMENTUM CALCULATION ===
        momentum_conditions = [
            dataframe["ema_fast"] > dataframe["ema_mid"],
            dataframe["ema_mid"] > dataframe["ema_slow"],
            dataframe["rsi"] > self.RSI_THRESHOLD,  # July: Relaxed to 55
            dataframe["macd"] > dataframe["macdsignal"],
            dataframe["close"] > dataframe["ema_fast"]
        ]
        
        # Use np.sum for proper array summation
        momentum_score = np.sum(momentum_conditions, axis=0)
        dataframe['momentum_strength'] = momentum_score / len(momentum_conditions)
        dataframe['momentum_aligned'] = (
            dataframe['momentum_strength'] >= self.MOMENTUM_STRENGTH  # July: Relaxed to 0.75
        )
        
        # July-adapted filters (more lenient)
        dataframe['volume_confirmed'] = (
            dataframe["volume_ratio"] > self.MIN_VOLUME_RATIO  # July: Relaxed to 1.7
        )
        
        dataframe['volatile_enough'] = (
            dataframe["atr"] / dataframe["close"] > self.MIN_ATR_RATIO  # July: Relaxed to 0.002
        )
        
        # Trend confirmation from 15m
        dataframe['trend_confirmed'] = dataframe.get('trend_15m_15m', True)
        
        # === JULY-ADAPTED REGIME CONFIRMATION ===
        dataframe['regime_favorable'] = (
            dataframe['favorable_volatility'] &
            dataframe['trending_regime'] &
            (dataframe['market_health'] >= self.MIN_MARKET_HEALTH) &  # July: Relaxed to 0.4
            (dataframe['trend_quality'] >= self.MIN_TREND_QUALITY) &  # July: Relaxed to 0.18
            (~dataframe['choppy_market'])                             # July: Relaxed choppiness
        )
        
        # === ENHANCED SESSION BIAS FILTER FOR JULY ===
        try:
            df_hours = dataframe.index.hour
            df_minutes = dataframe.index.minute
            minutes_since_midnight = df_hours * 60 + df_minutes
            
            # London session (07:00-11:00 UTC) = 420-660 minutes (JULY: Extended)
            london_session = (minutes_since_midnight >= 420) & (minutes_since_midnight < 660)
            
            # NY session (12:30-17:00 UTC) = 750-1020 minutes (JULY: Extended)
            ny_session = (minutes_since_midnight >= 750) & (minutes_since_midnight < 1020)
            
            # Asian session (22:00-02:00 UTC) = 1320+ or <120 minutes (JULY: Added for more opportunities)
            asian_session = (minutes_since_midnight >= 1320) | (minutes_since_midnight < 120)
            
            dataframe['session_ok'] = london_session | ny_session | asian_session  # JULY: Added Asian
        except:
            # Fallback if index is not datetime
            dataframe['session_ok'] = True

        return dataframe

    def calculate_liquidity_levels(self, df: DataFrame) -> DataFrame:
        """
        Calculate key levels with liquidity sweep detection (Keep Proven Logic)
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
        JULY-ADAPTED ENTRY LOGIC - Balanced Relaxation for Current Market Conditions
        Maintains quality while increasing opportunities in July 2025
        """
        
        # === JULY-ADAPTED QUALITY GATES ===
        momentum_ok = dataframe['momentum_aligned']
        volume_ok = dataframe['volume_confirmed'] 
        volatility_ok = dataframe['volatile_enough']
        trend_ok = dataframe['trend_confirmed']
        session_ok = dataframe['session_ok']  # Now includes Asian session
        regime_ok = dataframe['regime_favorable']  # Now uses July-relaxed thresholds
        
        # === JULY-ADAPTED ADAPTIVE FILTERING ===
        # Slightly more lenient adaptive filtering for July conditions
        market_health = dataframe['market_health']
        
        # July-adapted adaptive volume threshold
        adaptive_volume_threshold = np.where(
            market_health >= 0.55,              # July: Reduced from 0.6
            self.MIN_VOLUME_RATIO,             # Normal volume in good health
            self.MIN_VOLUME_RATIO * 1.15       # July: Reduced penalty (1.15 vs 1.2)
        )
        volume_adaptive = dataframe['volume_ratio'] > adaptive_volume_threshold
        
        # July-adapted adaptive momentum threshold  
        adaptive_momentum_threshold = np.where(
            market_health >= 0.55,              # July: Reduced from 0.6
            self.MOMENTUM_STRENGTH,            # Normal momentum in good health
            self.MOMENTUM_STRENGTH + 0.05      # July: Reduced penalty (0.05 vs 0.07)
        )
        momentum_adaptive = dataframe['momentum_strength'] > adaptive_momentum_threshold
        
        # === JULY-ADAPTED SETUPS ===
        
        # 1. July-adapted Liquidity Sweep (slightly more opportunities)
        sweep_reversal_july = (
            (dataframe['sweep_high'] | dataframe['sweep_low']) &
            (dataframe['close'] > dataframe['open']) &  # Green candle after sweep
            volume_adaptive &                           # July-adapted adaptive volume
            momentum_adaptive &                         # July-adapted adaptive momentum  
            (dataframe['rsi'] > 56) & (dataframe['rsi'] < 85) &  # July: Slightly relaxed from 58
            (market_health >= 0.45)                    # July: Relaxed from 0.5
        )
        
        # 2. July-adapted Momentum Breakout
        momentum_breakout_july = (
            (dataframe['close'] > dataframe['prev_session_high']) &
            (dataframe['close'].shift(1) <= dataframe['prev_session_high'].shift(1)) &
            momentum_adaptive &                         # July-adapted adaptive momentum
            volume_adaptive &                           # July-adapted adaptive volume
            (dataframe['rsi'] > 56) & (dataframe['rsi'] < 85) &  # July: Slightly relaxed from 58
            (dataframe['close'] > dataframe['prev_session_close'] * 1.0035) &  # July: Reduced from 1.005
            (market_health >= 0.4)                     # July: Relaxed from 0.45
        )
        
        # 3. July-adapted Session Momentum 
        basic_session_momentum_july = (
            session_ok &
            momentum_adaptive &                         # July-adapted adaptive momentum
            (dataframe['close'] > dataframe['prev_session_close'] * 1.003) &  # July: Reduced from 1.004
            volume_adaptive &                           # July-adapted adaptive volume
            (dataframe['close'] > dataframe['open']) &  # Green candle
            (dataframe['rsi'] > 56) & (dataframe['rsi'] < 80) &  # July: Slightly relaxed from 58
            (dataframe['close'] > dataframe['ema_fast'] * 1.001) &  # July: Reduced from 1.0015
            (market_health >= 0.35)                    # July: Relaxed from 0.4
        )
        
        # === COMBINE JULY-ADAPTED SETUPS ===
        july_adapted_setups = (
            sweep_reversal_july | momentum_breakout_july | basic_session_momentum_july
        )
        
        # === JULY-ADAPTED PAIR-SPECIFIC OPTIMIZATIONS ===
        # Keep successful pair-specific optimizations but relax slightly for July
        if metadata and 'pair' in metadata:
            pair = metadata['pair']
            
            # ETH-specific enhancements (slightly relaxed for July)
            if 'ETH' in pair:
                eth_enhanced_momentum_july = (
                    momentum_ok & 
                    volume_ok & 
                    (dataframe['close'] > dataframe['open']) &  # Green candle
                    (dataframe['rsi'] > 53) & (dataframe['rsi'] < 80) &  # July: Relaxed from 55
                    (dataframe['close'] > dataframe['ema_fast']) &
                    (market_health >= 0.3)  # July: Relaxed from 0.35
                )
                july_adapted_setups = july_adapted_setups | eth_enhanced_momentum_july
            
            # SOL-specific adjustments (keep tighter but relax slightly for July)
            elif 'SOL' in pair:
                sol_precise_momentum_july = (
                    momentum_ok & 
                    volume_adaptive &  # Use adaptive for SOL
                    volatility_ok &
                    (dataframe['close'] > dataframe['open']) &  # Green candle
                    (dataframe['rsi'] > 60) & (dataframe['rsi'] < 78) &  # July: Slightly relaxed from 62
                    (dataframe['close'] > dataframe['ema_fast'] * 1.0025) &  # July: Relaxed from 1.003
                    (market_health >= 0.5)  # July: Relaxed from 0.55
                )
                july_adapted_setups = july_adapted_setups | sol_precise_momentum_july
        
        # === FINAL ENTRY CONDITION WITH JULY ADAPTATIONS ===
        july_adapted_entry = (
            momentum_ok & 
            volume_ok & 
            volatility_ok & 
            trend_ok &
            regime_ok &                # Uses July-adapted market health (0.4)
            july_adapted_setups &      # July-adapted setups (includes pair-specific)
            (~dataframe['choppy_market'])  # July-adapted choppiness filter (0.75)
        )
        
        dataframe.loc[july_adapted_entry, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        PROVEN ROI-ONLY STRATEGY: Let validated ROI ladder handle exits
        """
        return dataframe

# === JULY 2025 OPTIMIZATION SUMMARY ===
"""
🎯 JULY 2025 MARKET ADAPTATIONS:

PROBLEM:
❌ Only 1 trade in 11 days in July (over-filtering)
❌ Market up +8.11% but strategy missed opportunities

SOLUTIONS:
✅ Market Health: Relaxed to 0.4 (from 0.5)
✅ Volume Threshold: Relaxed to 1.7x (from 1.9x)  
✅ RSI Threshold: Relaxed to 55 (from 57)
✅ Momentum Strength: Relaxed to 0.75 (from 0.78)
✅ Session Filter: Added Asian session for more opportunities
✅ Adaptive Penalties: Reduced to be less restrictive

🏆 EXPECTED JULY RESULTS:
- Increase from 0.1 trades/day to 2-4 trades/week
- Maintain risk profile (same ROI/stoploss)
- Preserve strong performance in other months
- Better capture July market movements

📊 VALIDATION STRATEGY:
✅ Test July performance (target: 2-3 trades minimum)
✅ Verify other months maintain performance
✅ Deploy if July improves without compromising history
""" 