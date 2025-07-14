# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file

"""
Crypto Scalping Optimized v8 - ULTRA-AGGRESSIVE FOR 3% MONTHLY 🎯
================================================================

PERFORMANCE ANALYSIS:
- Enhanced v7: +0.50% over 6 months (+0.27% in best month)
- Target: 3% monthly (need 11x improvement even in best month!)
- Current: 0.08% monthly average → Need 3% monthly

🎯 ULTRA-AGGRESSIVE STRATEGY FOR 3% MONTHLY:
- MAXIMUM ROI targets: 3.0%/2.5%/2.0% (vs 2.0%/1.5%/1.0%)
- ULTRA-PREMIUM filters: Only absolute best setups
- MAXIMUM momentum/volume requirements
- AGGRESSIVE but controlled risk management

💡 ULTRA-OPTIMIZATION APPROACH:
- ROI ladder: 3.0%/2.5%/2.0% (3x higher than v7)
- Ultra-tight entry filters (top 1% setups only)  
- Maximum momentum (85%+) and volume (2.5x+)
- Shortest time to profit (10min/30min targets)

🏆 MISSION: ACHIEVE 3% MONTHLY OR BUST!
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
    ULTRA-AGGRESSIVE FOR 3% MONTHLY: Maximum ROI + Ultra-Premium Setups
    Monthly target: +3% = 36% annual compound growth
    Ultra-aggressive ROI targets with ultra-premium quality filters
    """

    INTERFACE_VERSION = 3
    timeframe: str = "5m"
    can_short: bool = False
    startup_candle_count: int = 300

    # === ULTRA-AGGRESSIVE ROI LADDER FOR 3% MONTHLY ===
    minimal_roi: Dict[str, float] = {
        "0": 0.030,     # 3.0% immediate (vs 2.0%)
        "10": 0.025,    # 2.5% after 10 min (vs 1.5% at 20min)
        "30": 0.020     # 2.0% after 30 min (vs 1.0% at 1h)
    }
    
    # === ULTRA-TIGHT STOPLOSS (Maximum Risk Control) ===
    stoploss: float = -0.04  # 4% vs 6% (ultra-tight)
    trailing_stop = False
    
    # === ULTRA-PREMIUM ENTRY PARAMETERS (Top 1% Setups Only) ===
    MIN_VOLUME_RATIO = 2.5       # 1.8 → 2.5 (massive volume confirmation)
    RSI_THRESHOLD = 65           # 55 → 65 (very strong momentum)
    LEVEL_PROXIMITY = 0.005      # 0.8% → 0.5% (ultra-tight levels)
    MOMENTUM_STRENGTH = 0.85     # 0.75 → 0.85 (ultra-strong momentum)
    MIN_ATR_RATIO = 0.0025       # 0.2% → 0.25% (ultra-volatile moves)

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
        ULTRA-PREMIUM ENTRY LOGIC - Top 1% Setups Only for 3% Monthly
        Only absolute highest quality setups with maximum confirmation
        """
        
        # === ULTRA-PREMIUM QUALITY GATES ===
        momentum_ok = dataframe['momentum_aligned']
        volume_ok = dataframe['volume_confirmed'] 
        volatility_ok = dataframe['volatile_enough']
        trend_ok = dataframe['trend_confirmed']
        session_ok = dataframe['session_ok']
        
        # === ULTRA-PREMIUM SETUPS (Top 1% Quality Only) ===
        
        # 1. Ultra liquidity sweep reversal (maximum probability)
        ultra_sweep_reversal = (
            (dataframe['sweep_high'] | dataframe['sweep_low']) &
            (dataframe['close'] > dataframe['open']) &  # Green candle after sweep
            (dataframe['volume_ratio'] > 3.0) &         # MASSIVE volume (vs 2.2)
            (dataframe['momentum_strength'] > 0.90) &   # Ultra momentum (vs 0.80)
            (dataframe['rsi'] > 70) & (dataframe['rsi'] < 85)  # Very strong but not extreme
        )
        
        # 2. Ultra momentum breakout (premium quality only)
        ultra_momentum_breakout = (
            (dataframe['close'] > dataframe['prev_session_high']) &
            (dataframe['close'].shift(1) <= dataframe['prev_session_high'].shift(1)) &
            (dataframe['momentum_strength'] > 0.90) &   # Ultra momentum (vs 0.85)
            (dataframe['volume_ratio'] > 2.8) &         # Ultra volume (vs 2.0)
            (dataframe['rsi'] > 70) &                   # Very strong RSI (vs 60)
            (dataframe['rsi'] < 85) &                   # But not overbought
            (dataframe['close'] > dataframe['prev_session_close'] * 1.008)  # Strong above session
        )
        
        # 3. Ultra session momentum (absolute premium)
        ultra_session_momentum = (
            session_ok &
            (dataframe['momentum_strength'] > 0.90) &   # Ultra momentum
            (dataframe['close'] > dataframe['prev_session_close'] * 1.01) &  # Well above session
            (dataframe['volume_ratio'] > 3.0) &         # MASSIVE volume
            (dataframe['close'] > dataframe['open']) &  # Green candle
            (dataframe['rsi'] > 65) & (dataframe['rsi'] < 80) &  # Strong RSI range
            (dataframe['close'] > dataframe['ema_fast'] * 1.003)  # Well above EMA
        )
        
        # === COMBINE ONLY ULTRA-PREMIUM SETUPS ===
        ultra_premium_setups = (
            ultra_sweep_reversal | ultra_momentum_breakout | ultra_session_momentum
        )
        
        # === ULTRA-PREMIUM ENTRY CONDITION (All Gates + Ultra Setups) ===
        ultra_premium_entry = (
            momentum_ok & 
            volume_ok & 
            volatility_ok & 
            trend_ok &
            session_ok &           # Session filter always required
            ultra_premium_setups   # Only ultra-premium quality setups
        )
        
        dataframe.loc[ultra_premium_entry, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        ULTRA-AGGRESSIVE ROI-ONLY STRATEGY: No custom exit signals
        Let ultra-aggressive ROI ladder handle all exits with 3%+ targets
        """
        return dataframe

    # === NO CUSTOM EXIT LOGIC - ULTRA-AGGRESSIVE ROI-ONLY ===
    # Ultra-aggressive ROI ladder does all the work with maximum profit targets

# === ULTRA-AGGRESSIVE STRATEGY TARGETS FOR 3% MONTHLY ===
"""
🎯 ULTRA-AGGRESSIVE STRATEGY FOR 3% MONTHLY RETURNS:

CURRENT PERFORMANCE ANALYSIS:
- Enhanced v7: +0.50% over 6 months (+0.27% in best month)
- Target: 3% monthly (need 11x improvement!)
- Ultra-aggressive approach required

ULTRA-OPTIMIZATION APPROACH:
1. MAXIMUM ROI targets: 3.0%/2.5%/2.0% (3x higher than v7)
2. Ultra-premium quality: Top 1% setups only
3. MASSIVE volume confirmation: 2.5x-3.0x average
4. Ultra-fast profit taking: 10min/30min vs 20min/60min

🏆 EXPECTED RESULTS:
- Very few but ultra-high quality trades
- MAXIMUM profit per trade (target 2-3% avg)
- Ultra-fast profit realization (10-30 min)
- Target: 3% monthly = 36% annual compound

📊 ULTRA-SUCCESS METRICS:
✅ 3% monthly return target (minimum requirement)
✅ Ultra-high profit per trade (target 2-3% avg)
✅ Ultra-fast execution (10-30 min trades)
✅ Maximum quality filtering (top 1% setups)
✅ Ultra-controlled risk (4% stoploss)

🏆 MISSION: 3% MONTHLY OR BUST!
Ultra-aggressive approach for maximum monthly returns!
""" 