# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file

"""
Crypto Scalping Optimized v11 - MARKET HEALTH ENHANCEMENT 🎯
============================================================

NEGATIVE MONTH ANALYSIS RESULTS:
- March 2025: 60% ROI rate, choppy bearish market (-12.21%)
- May 2025: 54% ROI rate, choppy bullish market (+19.37%)
- Problem: Choppy conditions cause ~50-60% ROI rate vs 70%+ needed

🔧 MARKET HEALTH ENHANCEMENTS:
1. CHOPPINESS FILTER: Detect ranging/sideways markets
2. TREND QUALITY: Avoid weak/choppy trends  
3. ADAPTIVE FILTERING: Stricter requirements in poor conditions
4. MARKET HEALTH SCORE: Composite health indicator

🎯 TARGET: Eliminate negative months by avoiding choppy conditions
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
    MARKET HEALTH AWARE SCALPING - Avoid Choppy Conditions
    Enhanced with choppiness detection and adaptive filtering
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
    
    # === NEW: MARKET HEALTH THRESHOLDS ===
    MIN_MARKET_HEALTH = 0.6      # Minimum market health score (0-1)
    MIN_TREND_QUALITY = 0.3      # Minimum trend quality score
    MAX_CHOPPINESS = 0.6         # Maximum choppiness tolerance

    def informative_pairs(self) -> List[Tuple[str, str]]:
        pairs = []
        if self.dp and self.dp.current_whitelist():
            for pair in self.dp.current_whitelist():
                pairs.append((pair, "15m"))  # Keep 15m for trend context
        return pairs

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Enhanced indicator stack with market health awareness"""
        
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
        
        # === ADVANCED MARKET HEALTH DETECTION ===
        
        # 1. Choppiness Index (detect ranging markets)
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
        
        dataframe['choppiness'] = choppiness_index(dataframe, 20)
        dataframe['choppy_market'] = dataframe['choppiness'] > 60  # >60 = choppy
        
        # 2. Trend Quality Assessment  
        # EMA alignment strength
        ema_aligned = (
            (dataframe["ema_fast"] > dataframe["ema_mid"]) & 
            (dataframe["ema_mid"] > dataframe["ema_slow"])
        )
        dataframe['ema_alignment'] = ema_aligned.rolling(10).sum() / 10  # 0-1 score
        
        # Trend consistency (price stays above/below EMA)
        price_above_ema = dataframe['close'] > dataframe['ema_fast']
        dataframe['trend_consistency'] = price_above_ema.rolling(20).sum() / 20  # 0-1 score
        
        # Combined trend quality
        dataframe['trend_quality'] = (dataframe['ema_alignment'] + dataframe['trend_consistency']) / 2
        
        # 3. Market Health Score (composite)
        # Higher volatility = better for scalping (but not extreme)
        dataframe['atr_percentile'] = dataframe['atr'].rolling(50).rank(pct=True)
        vol_score = np.where(
            (dataframe['atr_percentile'] > 0.3) & (dataframe['atr_percentile'] < 0.8),
            1.0,  # Good volatility range
            0.5   # Too low or too high
        )
        
        # Volume health  
        vol_health = np.where(dataframe['volume_ratio'] > 1.2, 1.0, 0.5)
        
        # Non-choppy market bonus
        chop_penalty = np.where(dataframe['choppy_market'], 0.3, 1.0)
        
        # Composite market health (0-1 scale)
        dataframe['market_health'] = (
            (dataframe['trend_quality'] * 0.4) +  # 40% trend quality
            (vol_score * 0.3) +                   # 30% volatility
            (vol_health * 0.2) +                  # 20% volume  
            (chop_penalty * 0.1)                  # 10% choppiness penalty
        )
        
        # === EXISTING REGIME DETECTION (Enhanced) ===
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
        
        # === ENHANCED: REGIME CONFIRMATION WITH MARKET HEALTH ===
        dataframe['regime_favorable'] = (
            dataframe['favorable_volatility'] &
            dataframe['trending_regime'] &
            (dataframe['market_health'] >= self.MIN_MARKET_HEALTH) &  # NEW: Market health
            (dataframe['trend_quality'] >= self.MIN_TREND_QUALITY) &  # NEW: Trend quality
            (~dataframe['choppy_market'])                             # NEW: Avoid choppy markets
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
        MARKET HEALTH AWARE ENTRY LOGIC - Avoid Choppy Conditions
        Enhanced filtering to eliminate negative month patterns
        """
        
        # === ENHANCED QUALITY GATES WITH MARKET HEALTH ===
        momentum_ok = dataframe['momentum_aligned']
        volume_ok = dataframe['volume_confirmed'] 
        volatility_ok = dataframe['volatile_enough']
        trend_ok = dataframe['trend_confirmed']
        session_ok = dataframe['session_ok']
        regime_ok = dataframe['regime_favorable']  # Already includes market health
        
        # === ADAPTIVE FILTERING BASED ON MARKET HEALTH ===
        # In poor market health, require stronger confirmation
        market_health = dataframe['market_health']
        
        # Adaptive volume threshold (higher when market health is poor)
        adaptive_volume_threshold = np.where(
            market_health >= 0.7, 
            self.MIN_VOLUME_RATIO,           # Normal volume in good health
            self.MIN_VOLUME_RATIO * 1.3      # Higher volume in poor health
        )
        volume_adaptive = dataframe['volume_ratio'] > adaptive_volume_threshold
        
        # Adaptive momentum threshold  
        adaptive_momentum_threshold = np.where(
            market_health >= 0.7,
            self.MOMENTUM_STRENGTH,          # Normal momentum in good health
            self.MOMENTUM_STRENGTH + 0.1     # Higher momentum in poor health
        )
        momentum_adaptive = dataframe['momentum_strength'] > adaptive_momentum_threshold
        
        # === ENHANCED SETUPS WITH MARKET HEALTH REQUIREMENTS ===
        
        # 1. Market Health Aware Liquidity Sweep
        health_sweep_reversal = (
            (dataframe['sweep_high'] | dataframe['sweep_low']) &
            (dataframe['close'] > dataframe['open']) &  # Green candle after sweep
            volume_adaptive &                           # Adaptive volume
            momentum_adaptive &                         # Adaptive momentum  
            (dataframe['rsi'] > 65) & (dataframe['rsi'] < 85) &
            (market_health >= 0.7)                     # Require good market health
        )
        
        # 2. High Quality Momentum Breakout
        health_momentum_breakout = (
            (dataframe['close'] > dataframe['prev_session_high']) &
            (dataframe['close'].shift(1) <= dataframe['prev_session_high'].shift(1)) &
            momentum_adaptive &                         # Adaptive momentum
            volume_adaptive &                           # Adaptive volume
            (dataframe['rsi'] > 65) & (dataframe['rsi'] < 85) &
            (dataframe['close'] > dataframe['prev_session_close'] * 1.006) &
            (market_health >= 0.6)                     # Allow slightly lower health for breakouts
        )
        
        # 3. Premium Session Momentum (Best Health Only)
        premium_session_momentum = (
            session_ok &
            momentum_adaptive &                         # Adaptive momentum
            (dataframe['close'] > dataframe['prev_session_close'] * 1.008) &
            volume_adaptive &                           # Adaptive volume
            (dataframe['close'] > dataframe['open']) &  # Green candle
            (dataframe['rsi'] > 60) & (dataframe['rsi'] < 80) &
            (dataframe['close'] > dataframe['ema_fast'] * 1.002) &
            (market_health >= 0.8)                     # Premium health only
        )
        
        # === COMBINE MARKET HEALTH AWARE SETUPS ===
        health_aware_setups = (
            health_sweep_reversal | health_momentum_breakout | premium_session_momentum
        )
        
        # === FINAL ENTRY CONDITION WITH ENHANCED FILTERING ===
        market_health_entry = (
            momentum_ok & 
            volume_ok & 
            volatility_ok & 
            trend_ok &
            session_ok &
            regime_ok &                # Includes market health requirements
            health_aware_setups &      # Market health aware setups
            (~dataframe['choppy_market'])  # Explicit choppiness filter
        )
        
        dataframe.loc[market_health_entry, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        BALANCED ROI-ONLY STRATEGY: Let optimized ROI ladder handle exits
        """
        return dataframe

# === MARKET HEALTH OPTIMIZATION SUMMARY ===
"""
🎯 MARKET HEALTH ENHANCEMENTS TO ELIMINATE NEGATIVE MONTHS:

CHOPPINESS DETECTION:
❌ Old: Blind trading in all conditions
✅ New: Choppiness Index filter (avoid ranging markets)

TREND QUALITY:
❌ Old: Basic EMA alignment  
✅ New: Trend quality score (consistency + alignment)

MARKET HEALTH SCORE:
❌ Old: Simple regime filters
✅ New: Composite health (trend + volatility + volume + choppiness)

ADAPTIVE FILTERING:
❌ Old: Fixed thresholds
✅ New: Stricter requirements when market health poor

🏆 EXPECTED RESULTS:
- Eliminate choppy market trading (cause of negative months)
- Higher ROI rate: 70%+ vs 50-60% in poor conditions  
- Fewer but higher quality trades
- Consistent positive monthly performance
- No more May/March style negative months

📊 TARGET METRICS:
✅ No months with <65% ROI rate
✅ Consistent 0.2%+ monthly returns
✅ Eliminate choppy condition trading
✅ Maintain 1-2% annual growth with low risk
""" 