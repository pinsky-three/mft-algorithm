# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file

"""
Crypto Scalping Phase 3 Practical v1.0 - SIMPLIFIED CONSISTENCY 🚀
==================================================================

ADDRESSING PHASE 3 OVER-ENGINEERING ISSUE:

❌ PHASE 3 PROBLEM: Over-engineered with too many complex filters
- 9+ simultaneous filter requirements
- Complex smart money detection
- Multi-layer scoring systems
- Result: 0 trades (analysis paralysis)

✅ PHASE 3 PRACTICAL SOLUTION: Best innovations + practical entry logic
- Keep: Adaptive targets, performance feedback, consistency engine
- Simplify: Entry conditions, volume analysis, regime detection
- Target: Actual trades with improved consistency

🎯 PRACTICAL APPROACH:
1. ✅ Keep adaptive profit targets (works well)
2. ✅ Keep performance feedback (prevents overtrading)
3. ✅ Keep basic consistency engine (avoid bad conditions)
4. ✅ Simplify volume requirements (practical thresholds)
5. ✅ Simplify entry conditions (2-3 key filters vs 9+)
6. ✅ Keep monthly trade limits (prevent overtrading)

TARGET: 50-80 trades/month, 1.5-3.0% profit, 75%+ win rate
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

class CryptoScalpingPhase3Practical(IStrategy):
    """
    PHASE 3 PRACTICAL - Best innovations with simplified entry logic
    """

    INTERFACE_VERSION = 3
    timeframe: str = "1m"
    can_short: bool = False
    startup_candle_count: int = 400  # Reduced from 600
    
    # === ADAPTIVE ROI SYSTEM ===
    minimal_roi: Dict[str, float] = {
        "0": 0.10,  # High value - managed by adaptive exit logic
    }
    
    # === ADAPTIVE STOPLOSS SYSTEM ===
    stoploss: float = -0.08  # More conservative than Phase 3 (-0.15)
    trailing_stop = True
    trailing_stop_positive = 0.008
    trailing_stop_positive_offset = 0.012
    trailing_only_offset_is_reached = True
    
    # === SIMPLIFIED HYPEROPT PARAMETERS ===
    
    # Volume parameters (simplified)
    volume_ratio_min = DecimalParameter(1.5, 2.5, default=1.8, space="buy")
    volume_quality_threshold = DecimalParameter(0.6, 0.8, default=0.7, space="buy")
    
    # Performance feedback (keep from Phase 3)
    performance_lookback = IntParameter(15, 35, default=25, space="buy")
    win_rate_threshold = DecimalParameter(0.6, 0.8, default=0.7, space="buy")
    
    # Market health (simplified)
    market_health_min = DecimalParameter(0.4, 0.7, default=0.55, space="buy")
    
    # Adaptive targets (keep from Phase 3)
    volatility_target_multiplier = DecimalParameter(0.8, 1.5, default=1.2, space="sell")
    
    # === PRACTICAL PARAMETERS ===
    MIN_VOLUME_RATIO = 1.8  # Simplified vs complex smart money detection
    MIN_MARKET_HEALTH = 0.55  # More realistic vs 0.7-0.8
    RSI_THRESHOLD = 55  # More inclusive vs 58
    MAX_MONTHLY_TRADES = 80  # Keep overtrading protection
    
    def __init__(self, config: dict = None):
        super().__init__(config)
        
        # Performance tracking (simplified from Phase 3)
        self.recent_trades = deque(maxlen=25)
        self.monthly_trade_count = 0
        self.last_month = None

    def informative_pairs(self) -> List[Tuple[str, str]]:
        pairs = []
        if self.dp and self.dp.current_whitelist():
            for pair in self.dp.current_whitelist():
                # Simplified: only 15m for trend context
                pairs.append((pair, "15m"))
        return pairs

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Simplified indicators focusing on what works"""
        
        # === Core Technical Indicators ===
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=10)
        dataframe["ema_mid"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=50)
        
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        
        macd = ta.MACD(dataframe, fastperiod=12, slowperiod=26, signalperiod=9)
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]
        
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        
        # === Simplified Volume Analysis ===
        dataframe["volume_sma"] = ta.SMA(dataframe['volume'], timeperiod=20)
        dataframe["volume_ratio"] = dataframe['volume'] / dataframe["volume_sma"]
        
        # Simple volume quality (vs complex smart money detection)
        dataframe['volume_quality'] = np.where(
            (dataframe['volume_ratio'] > 1.5) & 
            (dataframe['close'] > dataframe['open']),  # Green candle
            np.clip(dataframe['volume_ratio'] / 3.0, 0.3, 1.0),  # Scale to 0.3-1.0
            np.clip(dataframe['volume_ratio'] / 4.0, 0.2, 0.7)   # Lower for red candles
        )
        
        # === Simplified Market Health ===
        dataframe['ema_alignment'] = (
            (dataframe['ema_fast'] > dataframe['ema_mid']) &
            (dataframe['ema_mid'] > dataframe['ema_slow'])
        ).astype(int)
        
        dataframe['trend_strength'] = dataframe['ema_alignment'].rolling(5).mean()
        dataframe['volatility_ok'] = (dataframe['atr'] / dataframe['close'] > 0.002)
        dataframe['volume_ok'] = (dataframe['volume_ratio'] > 1.3)
        
        # Simple market health score (vs complex multi-factor)
        health_factors = [
            dataframe['trend_strength'],
            dataframe['volatility_ok'].astype(float),
            dataframe['volume_ok'].astype(float),
            (dataframe['rsi'] > 30).astype(float),  # Not oversold
            (dataframe['rsi'] < 85).astype(float),  # Not overbought
        ]
        
        dataframe['market_health'] = np.mean(health_factors, axis=0)
        
        # === 15m Trend Context (simplified) ===
        if self.dp and metadata:
            try:
                informative_15m = self.dp.get_pair_dataframe(
                    pair=metadata["pair"], timeframe="15m"
                )
                
                informative_15m['ema_trend'] = ta.EMA(informative_15m, timeperiod=21)
                informative_15m['trend_15m'] = (
                    informative_15m['close'] > informative_15m['ema_trend']
                )
                
                dataframe = merge_informative_pair(
                    dataframe, informative_15m, self.timeframe, "15m", ffill=True
                )
                
            except Exception:
                dataframe['trend_15m_15m'] = True
        else:
            dataframe['trend_15m_15m'] = True
        
        # === Adaptive Targets (keep from Phase 3) ===
        dataframe = self._populate_adaptive_targets(dataframe)
        
        # === Performance Feedback (simplified from Phase 3) ===
        dataframe = self._populate_performance_feedback(dataframe)
        
        # === Basic Consistency Filters ===
        dataframe['avoid_bad_conditions'] = (
            (dataframe['volume_ratio'] < 0.8) |  # Very low volume
            (dataframe['atr'] / dataframe['close'] < 0.001) |  # Very low volatility
            (dataframe['rsi'] > 90) |  # Extreme overbought
            (dataframe['rsi'] < 10)    # Extreme oversold
        )
        
        return dataframe

    def _populate_adaptive_targets(self, dataframe: DataFrame) -> DataFrame:
        """Keep adaptive targets from Phase 3 - they work well"""
        
        # Base profit targets
        base_target_1 = 0.015  # 1.5%
        base_target_2 = 0.025  # 2.5%
        base_target_3 = 0.040  # 4.0%
        
        # Volatility adjustment
        atr_ratio = dataframe['atr'] / dataframe['close']
        volatility_multiplier = np.clip(atr_ratio / 0.003, 0.8, 1.5)
        
        # Volume adjustment
        volume_multiplier = np.clip(dataframe['volume_ratio'] / 2.0, 0.9, 1.3)
        
        # Market health adjustment
        health_multiplier = np.clip(dataframe['market_health'], 0.8, 1.2)
        
        # Combined multiplier
        total_multiplier = (
            volatility_multiplier * 
            volume_multiplier * 
            health_multiplier * 
            self.volatility_target_multiplier.value
        )
        
        dataframe['adaptive_target_1'] = base_target_1 * total_multiplier
        dataframe['adaptive_target_2'] = base_target_2 * total_multiplier
        dataframe['adaptive_target_3'] = base_target_3 * total_multiplier
        
        # Clamp targets to reasonable ranges
        dataframe['adaptive_target_1'] = np.clip(dataframe['adaptive_target_1'], 0.008, 0.025)
        dataframe['adaptive_target_2'] = np.clip(dataframe['adaptive_target_2'], 0.015, 0.040)
        dataframe['adaptive_target_3'] = np.clip(dataframe['adaptive_target_3'], 0.025, 0.060)
        
        return dataframe

    def _populate_performance_feedback(self, dataframe: DataFrame) -> DataFrame:
        """Simplified performance feedback from Phase 3"""
        
        # Get recent trade statistics
        if len(self.recent_trades) >= 5:
            recent_profits = [t['profit_percent'] for t in self.recent_trades]
            recent_wins = [p > 0 for p in recent_profits]
            
            recent_win_rate = np.mean(recent_wins)
            recent_avg_profit = np.mean(recent_profits)
            
        else:
            recent_win_rate = 0.75  # Optimistic default
            recent_avg_profit = 0.015  # Optimistic default
        
        # Apply to dataframe
        dataframe['recent_win_rate'] = recent_win_rate
        dataframe['recent_avg_profit'] = recent_avg_profit
        
        # Performance-based entry adjustment
        dataframe['performance_ok'] = (
            (recent_win_rate >= self.win_rate_threshold.value) |
            (len(self.recent_trades) < 5)  # Give benefit of doubt early
        )
        
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        PRACTICAL ENTRY LOGIC - Simplified but effective
        
        Focus on 3 key areas instead of 9+ complex filters:
        1. Basic momentum and trend
        2. Volume confirmation  
        3. Market health check
        """
        
        # === 1. BASIC MOMENTUM & TREND ===
        momentum_ok = (
            (dataframe['rsi'] > self.RSI_THRESHOLD) & (dataframe['rsi'] < 80) &
            (dataframe['macd'] > dataframe['macdsignal']) &
            (dataframe['close'] > dataframe['ema_fast']) &
            (dataframe['ema_fast'] > dataframe['ema_mid'])
        )
        
        # === 2. VOLUME CONFIRMATION ===
        volume_ok = (
            (dataframe['volume_ratio'] > self.volume_ratio_min.value) &
            (dataframe['volume_quality'] >= self.volume_quality_threshold.value)
        )
        
        # === 3. MARKET HEALTH CHECK ===
        market_ok = (
            (dataframe['market_health'] >= self.market_health_min.value) &
            (~dataframe['avoid_bad_conditions']) &
            (dataframe.get('trend_15m_15m', True))  # 15m trend support
        )
        
        # === 4. PERFORMANCE FEEDBACK ===
        performance_ok = dataframe['performance_ok']
        
        # === 5. MONTHLY TRADE LIMIT ===
        self._update_monthly_trade_count()
        monthly_ok = self.monthly_trade_count < self.MAX_MONTHLY_TRADES
        
        # === COMBINE CONDITIONS (Simple AND logic) ===
        practical_entry = (
            momentum_ok &
            volume_ok &
            market_ok &
            performance_ok &
            monthly_ok
        )
        
        dataframe.loc[practical_entry, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Exits handled by custom exit logic"""
        return dataframe

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float,
                    current_profit: float, **kwargs) -> Optional[str]:
        """Keep adaptive exit system from Phase 3"""
        
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if len(dataframe) < 1:
            return None
            
        last_candle = dataframe.iloc[-1].squeeze()
        trade_duration = (current_time - trade.open_date_utc).total_seconds() / 60
        
        # === ADAPTIVE PROFIT TARGETS ===
        target_1 = last_candle['adaptive_target_1']
        target_2 = last_candle['adaptive_target_2']
        target_3 = last_candle['adaptive_target_3']
        
        # Progressive exits
        if current_profit >= target_3:
            return "adaptive_max_target"
        elif current_profit >= target_2 and trade_duration > 2:
            return "adaptive_target_2"
        elif current_profit >= target_1 and trade_duration > 1:
            return "adaptive_target_1"
        
        # === BASIC STOP LOSS ===
        if current_profit <= -0.03:  # 3% stop loss
            return "stop_loss"
        
        # === TIME-BASED EXIT ===
        if trade_duration > 20:  # 20 minutes max
            if current_profit > 0.005:  # Small profit
                return "time_exit_profit"
            elif current_profit < -0.015:  # Cut losses
                return "time_exit_loss"
        
        return None

    def custom_stake_amount(self, pair: str, current_time: datetime, current_rate: float,
                           proposed_stake: float, min_stake: Optional[float], max_stake: float,
                           leverage: float, entry_tag: Optional[str], side: str,
                           **kwargs) -> float:
        """Simplified position sizing"""
        
        # Base sizing based on recent performance
        if len(self.recent_trades) >= 5:
            recent_profits = [t['profit_percent'] for t in self.recent_trades]
            recent_wins = [p > 0 for p in recent_profits]
            win_rate = np.mean(recent_wins)
            
            # Adjust size based on performance
            if win_rate >= 0.8:
                size_multiplier = 1.2  # Increase when doing well
            elif win_rate < 0.6:
                size_multiplier = 0.7  # Reduce when struggling
            else:
                size_multiplier = 1.0
        else:
            size_multiplier = 0.8  # Conservative start
        
        # Market condition adjustment
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if len(dataframe) > 0:
            last_candle = dataframe.iloc[-1].squeeze()
            health_multiplier = 0.7 + (last_candle['market_health'] * 0.3)  # 0.7-1.0 range
            size_multiplier *= health_multiplier
        
        calculated_stake = proposed_stake * np.clip(size_multiplier, 0.3, 1.5)
        
        # Ensure bounds
        if min_stake:
            calculated_stake = max(calculated_stake, min_stake)
        calculated_stake = min(calculated_stake, max_stake)
        
        return calculated_stake

    def _update_monthly_trade_count(self):
        """Track monthly trades to prevent overtrading"""
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
        """Record trade performance for feedback"""
        
        # Record trade for performance feedback
        trade_record = {
            'pair': pair,
            'profit_percent': trade.calc_profit_ratio(rate),
            'duration_minutes': (current_time - trade.open_date_utc).total_seconds() / 60,
            'exit_reason': exit_reason,
            'timestamp': current_time
        }
        
        self.recent_trades.append(trade_record)
        
        return True

# === PHASE 3 PRACTICAL SUMMARY ===
"""
🎯 PHASE 3 PRACTICAL IMPROVEMENTS:

✅ KEPT WHAT WORKS:
- Adaptive profit targets (market-responsive exits)
- Performance feedback system (prevents overtrading)
- Monthly trade limits (consistency)
- Basic consistency filters (avoid bad conditions)

✅ SIMPLIFIED WHAT DIDN'T:
- Entry conditions: 3 key filters vs 9+ complex ones
- Volume analysis: practical ratios vs complex smart money detection
- Market health: simple 5-factor score vs complex multi-layer
- No ML regime detection (caused over-filtering)
- No premium entry scoring (too restrictive)

🎯 PRACTICAL TARGETS:
- 50-80 trades per month (vs 0 in Phase 3)
- 1.5-3.0% monthly profit
- 75%+ win rate
- <0.15% drawdown
- Actual tradeable strategy

📊 EXPECTED RESULTS:
- Significantly more trades than Phase 3 (actual activity)
- Better consistency than Phase 2 (adaptive targets + feedback)
- Realistic entry conditions that can trigger
- Maintains best innovations while being practical
""" 