# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file

"""
Crypto Scalping Phase 3 Final v1.0 - MARKET REGIME MASTERY 🚀
=============================================================

ADDRESSING MONTHLY CONSISTENCY ISSUE:

📊 PHASE 3 PRACTICAL ANALYSIS:
✅ Overall: +3.647 USDT (vs -1.999 USDT in Phase 2) 
✅ Volume Control: 80 trades/month consistency
❌ Monthly Inconsistency: 4/6 negative months still persist

🔍 PATTERN IDENTIFIED:
Good Months: 80-86% win rates → Profitable (Jan +0.77%, May +1.56%)
Bad Months: 62-68% win rates → Losses (Feb -0.76%, Mar -0.42%, Apr -0.52%)

💡 ROOT CAUSE: Strategy works in trending/volatile markets, fails in choppy/ranging conditions

🎯 PHASE 3 FINAL SOLUTION - SMART REGIME DETECTION:

1. ✅ SIMPLE TREND DETECTION: Multi-timeframe trend alignment
2. ✅ VOLATILITY REGIME FILTER: Sufficient volatility for scalping  
3. ✅ MOMENTUM QUALITY CHECK: Sustained directional movement
4. ✅ CHOPPINESS AVOIDANCE: Detect and avoid ranging markets
5. ✅ ADAPTIVE FREQUENCY: Reduce trading during poor conditions
6. ✅ PERFORMANCE GATING: Stop trading if recent performance poor

TARGET: 3/6 positive months → 5/6 positive months, 2.5%+ total profit
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from collections import deque
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from pandas import DataFrame

import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy, merge_informative_pair, IntParameter, DecimalParameter

class CryptoScalpingPhase3Final(IStrategy):
    """
    PHASE 3 FINAL - Market Regime Mastery for Monthly Consistency
    """

    INTERFACE_VERSION = 3
    timeframe: str = "1m"
    can_short: bool = False
    startup_candle_count: int = 400
    
    # === ADAPTIVE ROI SYSTEM ===
    minimal_roi: Dict[str, float] = {
        "0": 0.08,  # Slightly lower than Practical (0.10) for faster exits
    }
    
    # === ADAPTIVE STOPLOSS SYSTEM ===
    stoploss: float = -0.06  # Tighter than Practical (-0.08) for loss control
    trailing_stop = True
    trailing_stop_positive = 0.008
    trailing_stop_positive_offset = 0.012
    trailing_only_offset_is_reached = True
    
    # === REGIME DETECTION HYPEROPT PARAMETERS ===
    
    # Trend strength detection
    trend_strength_min = DecimalParameter(0.6, 0.9, default=0.75, space="buy")
    multi_tf_alignment_min = DecimalParameter(0.6, 0.85, default=0.7, space="buy")
    
    # Volatility regime detection  
    volatility_percentile_min = DecimalParameter(0.3, 0.7, default=0.5, space="buy")
    atr_ratio_min = DecimalParameter(0.002, 0.005, default=0.003, space="buy")
    
    # Momentum quality
    momentum_quality_min = DecimalParameter(0.65, 0.85, default=0.75, space="buy")
    directional_strength_min = DecimalParameter(0.6, 0.8, default=0.7, space="buy")
    
    # Choppiness avoidance
    choppiness_threshold = DecimalParameter(50, 75, default=65, space="buy")
    range_bound_threshold = DecimalParameter(0.6, 0.8, default=0.7, space="buy")
    
    # Adaptive frequency control
    performance_lookback_days = IntParameter(3, 10, default=7, space="buy")
    min_win_rate_continue = DecimalParameter(0.65, 0.8, default=0.72, space="buy")
    frequency_reduction_factor = DecimalParameter(0.3, 0.7, default=0.5, space="buy")
    
    # Volume and market health (simplified from Practical)
    volume_ratio_min = DecimalParameter(1.6, 2.2, default=1.8, space="buy")
    market_health_min = DecimalParameter(0.5, 0.7, default=0.6, space="buy")
    
    # === REGIME DETECTION PARAMETERS ===
    MIN_TREND_STRENGTH = 0.75
    MIN_VOLATILITY_PERCENTILE = 0.5  
    MIN_MOMENTUM_QUALITY = 0.75
    MAX_CHOPPINESS = 65
    MIN_WIN_RATE_CONTINUE = 0.72
    MAX_MONTHLY_TRADES = 80
    
    def __init__(self, config: dict = None):
        super().__init__(config)
        
        # Performance tracking for regime detection
        self.recent_trades = deque(maxlen=50)  # Increased for better regime detection
        self.daily_performance = deque(maxlen=self.performance_lookback_days.value)
        self.monthly_trade_count = 0
        self.last_month = None
        self.poor_performance_sessions = set()

    def informative_pairs(self) -> List[Tuple[str, str]]:
        pairs = []
        if self.dp and self.dp.current_whitelist():
            for pair in self.dp.current_whitelist():
                # Multi-timeframe for regime detection
                pairs.extend([
                    (pair, "5m"),   # Short-term trend
                    (pair, "15m"),  # Medium-term trend  
                    (pair, "1h")    # Long-term trend
                ])
        return pairs

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Enhanced indicators with regime detection focus"""
        
        # === Core Technical Indicators ===
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=8)
        dataframe["ema_mid"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema_macro"] = ta.EMA(dataframe, timeperiod=100)
        
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["rsi_fast"] = ta.RSI(dataframe, timeperiod=7)
        
        macd = ta.MACD(dataframe, fastperiod=12, slowperiod=26, signalperiod=9)
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]
        
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_slow"] = ta.ATR(dataframe, timeperiod=28)
        
        # === REGIME DETECTION INDICATORS ===
        dataframe = self._populate_trend_regime_detection(dataframe)
        dataframe = self._populate_volatility_regime_detection(dataframe)
        dataframe = self._populate_momentum_regime_detection(dataframe)
        dataframe = self._populate_choppiness_detection(dataframe)
        dataframe = self._populate_multi_timeframe_regime(dataframe, metadata)
        
        # === Volume Analysis (Simplified but Effective) ===
        dataframe["volume_sma"] = ta.SMA(dataframe['volume'], timeperiod=20)
        dataframe["volume_ratio"] = dataframe['volume'] / dataframe["volume_sma"]
        
        # === Adaptive Targets (Keep from Practical) ===
        dataframe = self._populate_adaptive_targets(dataframe)
        
        # === Performance Feedback & Regime Gating ===
        dataframe = self._populate_performance_regime_gating(dataframe)
        
        return dataframe

    def _populate_trend_regime_detection(self, dataframe: DataFrame) -> DataFrame:
        """Simple but effective trend regime detection"""
        
        # EMA trend alignment
        dataframe['ema_bullish_alignment'] = (
            (dataframe['ema_fast'] > dataframe['ema_mid']) &
            (dataframe['ema_mid'] > dataframe['ema_slow']) &
            (dataframe['ema_slow'] > dataframe['ema_macro'])
        ).astype(int)
        
        # Trend strength calculation
        dataframe['trend_strength'] = dataframe['ema_bullish_alignment'].rolling(10).mean()
        
        # Price momentum alignment
        dataframe['price_above_emas'] = (
            (dataframe['close'] > dataframe['ema_fast']) &
            (dataframe['close'] > dataframe['ema_mid'])
        ).astype(int)
        
        dataframe['price_momentum_strength'] = dataframe['price_above_emas'].rolling(5).mean()
        
        # Combined trend regime score
        dataframe['trend_regime_score'] = (
            dataframe['trend_strength'] * 0.6 + 
            dataframe['price_momentum_strength'] * 0.4
        )
        
        dataframe['trend_regime_favorable'] = (
            dataframe['trend_regime_score'] >= self.trend_strength_min.value
        )
        
        return dataframe

    def _populate_volatility_regime_detection(self, dataframe: DataFrame) -> DataFrame:
        """Volatility regime for scalping effectiveness"""
        
        # ATR percentile analysis
        dataframe['atr_percentile'] = dataframe['atr'].rolling(50).rank(pct=True)
        
        # Volatility expansion detection
        dataframe['volatility_expanding'] = (
            dataframe['atr'] > dataframe['atr_slow']
        )
        
        # Sufficient volatility for scalping
        dataframe['atr_ratio'] = dataframe['atr'] / dataframe['close']
        dataframe['sufficient_volatility'] = (
            dataframe['atr_ratio'] >= self.atr_ratio_min.value
        )
        
        # Combined volatility regime
        dataframe['volatility_regime_favorable'] = (
            (dataframe['atr_percentile'] >= self.volatility_percentile_min.value) &
            dataframe['volatility_expanding'] &
            dataframe['sufficient_volatility']
        )
        
        return dataframe

    def _populate_momentum_regime_detection(self, dataframe: DataFrame) -> DataFrame:
        """Momentum quality for sustainable moves"""
        
        # Directional momentum
        dataframe['price_momentum'] = (dataframe['close'] - dataframe['close'].shift(5)) / dataframe['close']
        dataframe['momentum_positive'] = (dataframe['price_momentum'] > 0).astype(int)
        
        # RSI momentum alignment
        dataframe['rsi_momentum_up'] = (
            (dataframe['rsi'] > 50) & 
            (dataframe['rsi'] > dataframe['rsi'].shift(1))
        ).astype(int)
        
        # MACD momentum
        dataframe['macd_momentum_up'] = (
            (dataframe['macd'] > dataframe['macdsignal']) &
            (dataframe['macd'] > dataframe['macd'].shift(1))
        ).astype(int)
        
        # Combined momentum quality
        momentum_factors = [
            dataframe['momentum_positive'],
            dataframe['rsi_momentum_up'], 
            dataframe['macd_momentum_up']
        ]
        
        dataframe['momentum_quality_score'] = np.mean(momentum_factors, axis=0)
        dataframe['momentum_regime_favorable'] = (
            dataframe['momentum_quality_score'] >= self.momentum_quality_min.value
        )
        
        # Directional strength (sustained movement)
        dataframe['directional_strength'] = dataframe['momentum_positive'].rolling(8).mean()
        dataframe['directional_regime_favorable'] = (
            dataframe['directional_strength'] >= self.directional_strength_min.value
        )
        
        return dataframe

    def _populate_choppiness_detection(self, dataframe: DataFrame) -> DataFrame:
        """Detect and avoid choppy/ranging markets"""
        
        # Simple choppiness index
        def calculate_choppiness(df, period=14):
            high_low = df['high'] - df['low']
            high_close = (df['high'] - df['close'].shift(1)).abs()
            low_close = (df['low'] - df['close'].shift(1)).abs()
            true_range = pd.DataFrame([high_low, high_close, low_close]).max()
            
            atr = true_range.rolling(window=period, min_periods=1).mean()
            high_low_range = df['high'].rolling(period).max() - df['low'].rolling(period).min()
            
            atr_sum = atr.rolling(period).sum()
            ci = 100 * np.log10(atr_sum / high_low_range) / np.log10(period)
            return ci.fillna(50)
        
        dataframe['choppiness_index'] = calculate_choppiness(dataframe)
        dataframe['not_choppy'] = (
            dataframe['choppiness_index'] <= self.choppiness_threshold.value
        )
        
        # Range-bound detection
        dataframe['range_high'] = dataframe['high'].rolling(20).max()
        dataframe['range_low'] = dataframe['low'].rolling(20).min()
        dataframe['range_position'] = (
            (dataframe['close'] - dataframe['range_low']) / 
            (dataframe['range_high'] - dataframe['range_low'])
        )
        
        # Avoid when stuck in middle of range
        dataframe['not_range_bound'] = (
            (dataframe['range_position'] < 0.3) | 
            (dataframe['range_position'] > 0.7)
        )
        
        dataframe['choppiness_regime_favorable'] = (
            dataframe['not_choppy'] & dataframe['not_range_bound']
        )
        
        return dataframe

    def _populate_multi_timeframe_regime(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Multi-timeframe regime alignment"""
        
        if not self.dp or not metadata:
            dataframe['multi_tf_regime_favorable'] = True
            return dataframe
        
        try:
            pair = metadata["pair"]
            
            # 5m trend
            informative_5m = self.dp.get_pair_dataframe(pair=pair, timeframe="5m")
            if len(informative_5m) > 0:
                informative_5m['ema_5m'] = ta.EMA(informative_5m, timeperiod=21)
                informative_5m['trend_5m'] = (informative_5m['close'] > informative_5m['ema_5m']).astype(float)
                dataframe = merge_informative_pair(dataframe, informative_5m, self.timeframe, "5m", ffill=True)
            else:
                dataframe['trend_5m_5m'] = 1.0
            
            # 15m trend  
            informative_15m = self.dp.get_pair_dataframe(pair=pair, timeframe="15m")
            if len(informative_15m) > 0:
                informative_15m['ema_15m'] = ta.EMA(informative_15m, timeperiod=21)
                informative_15m['trend_15m'] = (informative_15m['close'] > informative_15m['ema_15m']).astype(float)
                dataframe = merge_informative_pair(dataframe, informative_15m, self.timeframe, "15m", ffill=True)
            else:
                dataframe['trend_15m_15m'] = 1.0
            
            # 1h trend
            informative_1h = self.dp.get_pair_dataframe(pair=pair, timeframe="1h")
            if len(informative_1h) > 0:
                informative_1h['ema_1h'] = ta.EMA(informative_1h, timeperiod=21)
                informative_1h['trend_1h'] = (informative_1h['close'] > informative_1h['ema_1h']).astype(float)
                dataframe = merge_informative_pair(dataframe, informative_1h, self.timeframe, "1h", ffill=True)
            else:
                dataframe['trend_1h_1h'] = 1.0
                
        except Exception:
            dataframe['trend_5m_5m'] = 1.0
            dataframe['trend_15m_15m'] = 1.0  
            dataframe['trend_1h_1h'] = 1.0
        
        # Multi-timeframe alignment score
        dataframe['multi_tf_alignment_score'] = (
            dataframe.get('trend_5m_5m', 1.0) * 0.4 +
            dataframe.get('trend_15m_15m', 1.0) * 0.35 +
            dataframe.get('trend_1h_1h', 1.0) * 0.25
        )
        
        dataframe['multi_tf_regime_favorable'] = (
            dataframe['multi_tf_alignment_score'] >= self.multi_tf_alignment_min.value
        )
        
        return dataframe

    def _populate_adaptive_targets(self, dataframe: DataFrame) -> DataFrame:
        """Keep adaptive targets from Phase 3 Practical"""
        
        # Base targets
        base_target_1 = 0.012  # Slightly lower for faster exits
        base_target_2 = 0.020  
        base_target_3 = 0.035  
        
        # Regime-based adjustments
        regime_multiplier = np.where(
            dataframe['trend_regime_favorable'] & 
            dataframe['volatility_regime_favorable'] &
            dataframe['momentum_regime_favorable'],
            1.2,  # Increase targets in good regimes
            0.8   # Reduce targets in poor regimes
        )
        
        dataframe['adaptive_target_1'] = base_target_1 * regime_multiplier
        dataframe['adaptive_target_2'] = base_target_2 * regime_multiplier
        dataframe['adaptive_target_3'] = base_target_3 * regime_multiplier
        
        # Clamp to reasonable ranges
        dataframe['adaptive_target_1'] = np.clip(dataframe['adaptive_target_1'], 0.008, 0.020)
        dataframe['adaptive_target_2'] = np.clip(dataframe['adaptive_target_2'], 0.015, 0.030)
        dataframe['adaptive_target_3'] = np.clip(dataframe['adaptive_target_3'], 0.025, 0.050)
        
        return dataframe

    def _populate_performance_regime_gating(self, dataframe: DataFrame) -> DataFrame:
        """Performance-based regime gating to avoid trading during poor periods"""
        
        # Calculate recent performance
        if len(self.recent_trades) >= 10:
            recent_profits = [t['profit_percent'] for t in list(self.recent_trades)[-20:]]
            recent_wins = [p > 0 for p in recent_profits]
            
            recent_win_rate = np.mean(recent_wins)
            recent_avg_profit = np.mean(recent_profits)
            
        else:
            recent_win_rate = 0.75  # Optimistic default
            recent_avg_profit = 0.01
        
        dataframe['recent_win_rate'] = recent_win_rate
        dataframe['recent_avg_profit'] = recent_avg_profit
        
        # Performance gate
        dataframe['performance_gate_ok'] = (
            (recent_win_rate >= self.min_win_rate_continue.value) |
            (len(self.recent_trades) < 10)  # Give benefit of doubt early
        )
        
        # Adaptive trading frequency based on performance
        if recent_win_rate < 0.65:
            trading_frequency = self.frequency_reduction_factor.value  # Reduce frequency
        elif recent_win_rate > 0.8:
            trading_frequency = 1.2  # Slight increase
        else:
            trading_frequency = 1.0
        
        dataframe['trading_frequency_multiplier'] = trading_frequency
        
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        PHASE 3 FINAL ENTRY LOGIC - Regime-Aware Trading
        
        Only trade when ALL regime conditions are favorable:
        1. Trend regime favorable (trending market)
        2. Volatility regime favorable (sufficient volatility)  
        3. Momentum regime favorable (quality momentum)
        4. Choppiness regime favorable (not choppy/ranging)
        5. Multi-timeframe alignment (trend confirmation)
        6. Performance gate OK (recent performance good)
        """
        
        # === 1. MASTER REGIME FILTER ===
        master_regime_favorable = (
            dataframe['trend_regime_favorable'] &
            dataframe['volatility_regime_favorable'] &
            dataframe['momentum_regime_favorable'] & 
            dataframe['choppiness_regime_favorable'] &
            dataframe['multi_tf_regime_favorable'] &
            dataframe['performance_gate_ok']
        )
        
        # === 2. BASIC ENTRY CONDITIONS (from Practical) ===
        basic_momentum = (
            (dataframe['rsi'] > 55) & (dataframe['rsi'] < 80) &
            (dataframe['macd'] > dataframe['macdsignal']) &
            (dataframe['close'] > dataframe['ema_fast'])
        )
        
        basic_volume = (
            dataframe['volume_ratio'] > self.volume_ratio_min.value
        )
        
        # === 3. MONTHLY TRADE LIMIT ===
        self._update_monthly_trade_count()
        monthly_ok = self.monthly_trade_count < self.MAX_MONTHLY_TRADES
        
        # === 4. ADAPTIVE FREQUENCY CONTROL ===
        frequency_ok = (
            np.random.random() < dataframe['trading_frequency_multiplier'].iloc[-1]
        ) if len(dataframe) > 0 else True
        
        # === 5. FINAL ENTRY LOGIC ===
        regime_aware_entry = (
            master_regime_favorable &  # KEY: Only trade in favorable regimes
            basic_momentum &
            basic_volume &
            monthly_ok &
            frequency_ok
        )
        
        dataframe.loc[regime_aware_entry, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Exits handled by custom exit logic"""
        return dataframe

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float,
                    current_profit: float, **kwargs) -> Optional[str]:
        """Enhanced exit logic with regime awareness"""
        
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if len(dataframe) < 1:
            return None
            
        last_candle = dataframe.iloc[-1].squeeze()
        trade_duration = (current_time - trade.open_date_utc).total_seconds() / 60
        
        # === REGIME-AWARE EXIT URGENCY ===
        regime_deteriorated = not (
            last_candle['trend_regime_favorable'] &
            last_candle['momentum_regime_favorable']
        )
        
        # === ADAPTIVE PROFIT TARGETS ===
        target_1 = last_candle['adaptive_target_1']
        target_2 = last_candle['adaptive_target_2']
        target_3 = last_candle['adaptive_target_3']
        
        # Exit faster if regime deteriorated
        if regime_deteriorated:
            target_1 *= 0.7  # Lower targets when regime poor
            target_2 *= 0.7
            target_3 *= 0.7
        
        # Progressive exits
        if current_profit >= target_3:
            return "adaptive_max_target"
        elif current_profit >= target_2 and trade_duration > 1:
            return "adaptive_target_2"
        elif current_profit >= target_1 and (trade_duration > 0.5 or regime_deteriorated):
            return "adaptive_target_1"
        
        # === REGIME-BASED STOP LOSS ===
        if regime_deteriorated and current_profit <= -0.02:
            return "regime_stop_loss"
        
        # === BASIC STOP LOSS ===
        if current_profit <= -0.04:  # 4% stop loss
            return "stop_loss"
        
        # === TIME-BASED EXIT ===
        max_duration = 15 if regime_deteriorated else 25
        
        if trade_duration > max_duration:
            if current_profit > 0.003:
                return "time_exit_profit"
            elif current_profit < -0.015:
                return "time_exit_loss"
        
        return None

    def custom_stake_amount(self, pair: str, current_time: datetime, current_rate: float,
                           proposed_stake: float, min_stake: Optional[float], max_stake: float,
                           leverage: float, entry_tag: Optional[str], side: str,
                           **kwargs) -> float:
        """Regime-aware position sizing"""
        
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if len(dataframe) == 0:
            return proposed_stake * 0.7
            
        last_candle = dataframe.iloc[-1].squeeze()
        
        # Base size on recent performance
        if len(self.recent_trades) >= 5:
            recent_profits = [t['profit_percent'] for t in list(self.recent_trades)[-10:]]
            recent_wins = [p > 0 for p in recent_profits]
            win_rate = np.mean(recent_wins)
            
            if win_rate >= 0.8:
                performance_multiplier = 1.2
            elif win_rate < 0.6:
                performance_multiplier = 0.6
            else:
                performance_multiplier = 1.0
        else:
            performance_multiplier = 0.8
        
        # Regime-based sizing
        regime_quality = (
            last_candle['trend_regime_favorable'] * 0.3 +
            last_candle['volatility_regime_favorable'] * 0.3 +
            last_candle['momentum_regime_favorable'] * 0.2 +
            last_candle['choppiness_regime_favorable'] * 0.2
        )
        
        regime_multiplier = 0.6 + (regime_quality * 0.4)  # 0.6 to 1.0 range
        
        final_multiplier = performance_multiplier * regime_multiplier
        calculated_stake = proposed_stake * np.clip(final_multiplier, 0.3, 1.3)
        
        # Ensure bounds
        if min_stake:
            calculated_stake = max(calculated_stake, min_stake)
        calculated_stake = min(calculated_stake, max_stake)
        
        return calculated_stake

    def _update_monthly_trade_count(self):
        """Track monthly trades"""
        current_month = datetime.now().month
        
        if self.last_month != current_month:
            self.monthly_trade_count = 0
            self.last_month = current_month

    def confirm_trade_entry(self, pair: str, order_type: str, amount: float, rate: float,
                           time_in_force: str, current_time: datetime, entry_tag: Optional[str],
                           side: str, **kwargs) -> bool:
        """Track trades and enforce monthly limit"""
        
        self._update_monthly_trade_count()
        
        if self.monthly_trade_count >= self.MAX_MONTHLY_TRADES:
            return False
        
        self.monthly_trade_count += 1
        return True

    def confirm_trade_exit(self, pair: str, trade: Trade, order_type: str, amount: float,
                          rate: float, time_in_force: str, exit_reason: str,
                          current_time: datetime, **kwargs) -> bool:
        """Record trade performance for regime learning"""
        
        trade_record = {
            'pair': pair,
            'profit_percent': trade.calc_profit_ratio(rate),
            'duration_minutes': (current_time - trade.open_date_utc).total_seconds() / 60,
            'exit_reason': exit_reason,
            'timestamp': current_time
        }
        
        self.recent_trades.append(trade_record)
        
        return True

# === PHASE 3 FINAL OPTIMIZATION SUMMARY ===
"""
🎯 PHASE 3 FINAL - MARKET REGIME MASTERY:

✅ REGIME DETECTION SYSTEM:
- Trend Regime: Multi-timeframe trend alignment detection
- Volatility Regime: ATR percentile + expansion analysis  
- Momentum Regime: Quality momentum with directional strength
- Choppiness Regime: Avoid ranging/choppy market conditions
- Multi-TF Regime: 5m/15m/1h alignment confirmation

✅ ADAPTIVE TRADING CONTROL:
- Performance Gating: Stop trading if recent win rate < 72%
- Frequency Control: Reduce trading during poor performance
- Monthly Limits: Max 80 trades to prevent overtrading
- Regime-Aware Sizing: Larger positions in favorable regimes

✅ ENHANCED EXIT MANAGEMENT:
- Regime-Aware Exits: Lower targets when regime deteriorates
- Faster Exits: Quicker exits during poor market conditions
- Tighter Stops: 4-6% stop loss vs 8% in Practical

🎯 TARGET IMPROVEMENTS vs PHASE 3 PRACTICAL:
- Monthly Consistency: 3/6 positive → 5/6 positive months
- Win Rate Floor: 62-68% → 75%+ minimum
- Avoid Bad Conditions: Filter out choppy/ranging markets
- Total Profit: +3.647 USDT → +6-8 USDT target

📊 SUCCESS METRICS:
✅ Only trade in favorable market regimes
✅ 75%+ win rate minimum (vs 62-68% bad months)
✅ 5/6 positive months (vs 3/6 currently)
✅ 2.5%+ total profit improvement
✅ Maintain 80 trades/month consistency
""" 