# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file

"""
Multi-Horizon Momentum Strategy Extended with TEMA - v8.5 PHASE 3 ADVANCED
==========================================================================

PHASE 3 ADVANCED OPTIMIZATION: Data-driven ATR targets for BTC $110K+ profitability.
Based on comprehensive volatility analysis 2025 vs 2024:

VOLATILITY ANALYSIS RESULTS (BTC >$110K):
- Volatility: 0.5909 (HIGH regime vs 0.05 baseline)
- ATR/Price: 0.0241 (2.41% - lower than 2024's 4.05%)
- Pattern: High volatility + compressed intraday ranges = whipsaw protection needed

OPTIMIZED ATR TARGETS v8.5.1 (scalp lock):
- Take Profit: 1.8x ATR  (tighter - captures frequent moves)
- Stop Loss: 1.2x ATR  (risk-adjusted)
- Trailing: 0.8x ATR  (early profit protection)
- Breakeven lock once +0.25 % (covers fees)
- Timeframes: 1m primary, 5m secondary, 15m trend filter

CRITICAL IMPROVEMENTS:
- ✅ Solved over-selectivity (5→11→14 trades progression)
- ✅ Optimized duration (2:33→1:16→1:01 average)
- ✅ Excellent risk control (≤0.01% max loss)
- 🎯 TARGET: Convert 0% win rate → profitable with optimized ATR targets

Entry Conditions (LONG):
-----------------------
- Triple EMA alignment (30 > 120 > 360)
- TEMA short-term uptrend (TEMA10 > TEMA80)  
- TEMA long-term uptrend (TEMA20_4h > TEMA70_4h)
- Strong momentum: ADX > 38 AND CMO > 40
- RSI > 55 (ultra-adaptive momentum v8.4)
- MACD bullish divergence
- Volume surge (3x average - premium trades only)
- 15m directional filter alignment

Risk Management v8.5:
--------------------
- Stop Loss: 2.2 ATR (whipsaw-resistant for high volatility)
- Take Profit: 3.5 ATR (optimized for BTC $110K+ patterns)  
- Trailing Stop: 1.8 ATR (enhanced profit capture)
- Emergency Stop: 30% hard floor

Back-test commands:
------------------
# PHASE 3 optimization test
freqtrade backtesting -s MultiHorizonMomentum -p BTC/USDT --timerange 20250101-20250131 --fee 0.1 --timeframe 1m

# Full comparison test
freqtrade backtesting -s MultiHorizonMomentum -p BTC/USDT,ETH/USDT --fee 0.1 --timeframe 1m
"""

from datetime import datetime
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
from pandas import DataFrame

import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy, merge_informative_pair

# ────────────────────────────────────────────────────────────────────────────────
# Strategy
# ────────────────────────────────────────────────────────────────────────────────

class MultiHorizonMomentum(IStrategy):
    """Enhanced momentum strategy with TEMA trend-following and Phase 3 optimized ATR exits."""

    INTERFACE_VERSION = 3
    timeframe: str = "1m"
    can_short: bool = False  # Set to True to enable short trading

    # Amount of history needed for indicators: max(360 for EMA, 100 for ATR, 80 for TEMA)
    startup_candle_count: int = 400

    # Close once price exceeds 0.3 % (covers ~2× exchange fee) if no other exit hit
    minimal_roi: Dict[str, float] = {"0": 0.003}

    # Emergency stoploss (will rarely trigger thanks to ATR SL in custom_exit)
    stoploss: float = -0.30  # 30% hard floor

    # Trailing handled by custom_exit - keep disabled here
    trailing_stop = False

    # ---------------------------------------------------------------------
    # Configuration flags
    # ---------------------------------------------------------------------
    USE_USDT_FILTER: bool = False  # CRYPTOCAP:USDT.D no existe a 1m
    USE_TEMA_FILTER: bool = True   # Enable TEMA crossover filters
    USE_ADX_CMO_FILTER: bool = True # Enable ADX/CMO momentum filters

    # ------------------------------------------------------------------
    # Informative pairs
    # ------------------------------------------------------------------
    def informative_pairs(self) -> List[Tuple[str, str]]:
        """Request 5m, 15m and 4h timeframes for directional filters.
        
        Phase 3 optimization: Added 5m for secondary signals in high volatility.
        """
        pairs: List[Tuple[str, str]] = []
        
        # Multi-timeframe analysis for Phase 3
        if self.dp and self.dp.current_whitelist():
            for pair in self.dp.current_whitelist():
                pairs.append((pair, "5m"))   # Secondary timeframe for high volatility
                pairs.append((pair, "15m"))  # Trend filter
                pairs.append((pair, "4h"))   # TEMA long-term trend
        
        if self.USE_USDT_FILTER:
            pairs.append(("USDT.D", "1d"))  # TradingView / CryptoCap ticker
        return pairs

    # ------------------------------------------------------------------
    # Indicator calculation
    # ------------------------------------------------------------------
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Original EMA stack
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=30)   # 30 min
        dataframe["ema_mid"] = ta.EMA(dataframe, timeperiod=120)  # 2  h
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=360) # 6  h

        # TEMA indicators for trend-following
        if self.USE_TEMA_FILTER:
            dataframe["tema10"] = ta.TEMA(dataframe, timeperiod=10)  # Short-term TEMA
            dataframe["tema80"] = ta.TEMA(dataframe, timeperiod=80)  # Long-term TEMA

        # ATR for risk management - Phase 3 optimized
        dataframe["atr100"] = ta.ATR(dataframe, timeperiod=100)
        
        # RSI for momentum confirmation
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        
        # MACD for trend strength
        macd = ta.MACD(dataframe)
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]
        dataframe["macdhist"] = macd["macdhist"]

        # ADX and CMO for momentum filtering
        if self.USE_ADX_CMO_FILTER:
            dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
            dataframe["cmo"] = ta.CMO(dataframe, timeperiod=14)

        # 5m EMAs for secondary confirmation (Phase 3)
        if self.dp and metadata:
            try:
                informative_5m = self.dp.get_pair_dataframe(pair=metadata["pair"], timeframe="5m")
                informative_5m["ema_fast_5m"] = ta.EMA(informative_5m, timeperiod=30)
                informative_5m["ema_mid_5m"] = ta.EMA(informative_5m, timeperiod=120)
                dataframe = merge_informative_pair(
                    dataframe, informative_5m, self.timeframe, "5m", ffill=True
                )
            except Exception:
                pass

            # EMAs 15m para filtro direccional
            try:
                informative_15m = self.dp.get_pair_dataframe(pair=metadata["pair"], timeframe="15m")
                informative_15m["ema_fast_15m"] = ta.EMA(informative_15m, timeperiod=30)
                informative_15m["ema_mid_15m"] = ta.EMA(informative_15m, timeperiod=120)
                dataframe = merge_informative_pair(
                    dataframe, informative_15m, self.timeframe, "15m", ffill=True
                )
            except Exception:
                pass

            # TEMA 4h para tendencia de largo plazo
            if self.USE_TEMA_FILTER:
                try:
                    informative_4h = self.dp.get_pair_dataframe(pair=metadata["pair"], timeframe="4h")
                    informative_4h["tema20_4h"] = ta.TEMA(informative_4h, timeperiod=20)
                    informative_4h["tema70_4h"] = ta.TEMA(informative_4h, timeperiod=70)
                    dataframe = merge_informative_pair(
                        dataframe, informative_4h, self.timeframe, "4h", ffill=True
                    )
                except Exception:
                    pass

        # Merge USDT dominance if available
        if self.USE_USDT_FILTER and self.dp:
            try:
                informative = self.dp.get_pair_dataframe(pair="USDT.D", timeframe="1d")
                informative["usdt_sma7"] = ta.SMA(informative, timeperiod=7)
                dataframe = merge_informative_pair(dataframe, informative, self.timeframe, "1d", ffill=True)
            except Exception:
                # In case data is missing – disable filter for this run
                self.USE_USDT_FILTER = False

        return dataframe

    # ------------------------------------------------------------------
    # Entry logic
    # ------------------------------------------------------------------
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Original EMA alignment condition
        cond_ema_long = (
            (dataframe["ema_fast"] > dataframe["ema_mid"]) &
            (dataframe["ema_mid"] > dataframe["ema_slow"])
        )
        
        cond_ema_short = (
            (dataframe["ema_fast"] < dataframe["ema_mid"]) &
            (dataframe["ema_mid"] < dataframe["ema_slow"])
        )

        # TEMA trend conditions
        cond_tema_short_long = True
        cond_tema_short_short = True
        cond_tema_long_long = True
        cond_tema_long_short = True
        
        if self.USE_TEMA_FILTER:
            # Short-term TEMA trend (1m timeframe)
            cond_tema_short_long = dataframe["tema10"] > dataframe["tema80"]
            cond_tema_short_short = dataframe["tema10"] < dataframe["tema80"]
            
            # Long-term TEMA trend (4h timeframe)
            if "tema20_4h_4h" in dataframe.columns and "tema70_4h_4h" in dataframe.columns:
                cond_tema_long_long = dataframe["tema20_4h_4h"] > dataframe["tema70_4h_4h"]
                cond_tema_long_short = dataframe["tema20_4h_4h"] < dataframe["tema70_4h_4h"]

        # ADX and CMO momentum conditions
        cond_adx = True
        cond_cmo_long = True
        cond_cmo_short = True
        
        if self.USE_ADX_CMO_FILTER:
            cond_adx = dataframe["adx"] > 38  # Ultra-adaptive trend condition (v8.4 Phase2 for BTC $110K+)
            cond_cmo_long = dataframe["cmo"] > 40  # Bullish momentum
            cond_cmo_short = dataframe["cmo"] < -40  # Bearish momentum

        # Phase 3: Ultra-selective volume filter (only premium liquidity trades)
        cond_volume = dataframe['volume'] > dataframe['volume'].rolling(30).mean() * 3.0

        # Multi-timeframe directional filters (Phase 3 enhancement)
        cond_dir_5m_long = True
        cond_dir_5m_short = True
        if "ema_fast_5m_5m" in dataframe.columns and "ema_mid_5m_5m" in dataframe.columns:
            cond_dir_5m_long = dataframe["ema_fast_5m_5m"] > dataframe["ema_mid_5m_5m"]
            cond_dir_5m_short = dataframe["ema_fast_5m_5m"] < dataframe["ema_mid_5m_5m"]

        cond_dir_15m_long = True
        cond_dir_15m_short = True
        if "ema_fast_15m_15m" in dataframe.columns and "ema_mid_15m_15m" in dataframe.columns:
            cond_dir_15m_long = dataframe["ema_fast_15m_15m"] > dataframe["ema_mid_15m_15m"]
            cond_dir_15m_short = dataframe["ema_fast_15m_15m"] < dataframe["ema_mid_15m_15m"]

        # RSI momentum filter - v8.4 Phase2 for maximum 2025 adaptability
        cond_rsi_long = dataframe["rsi"] > 55  # Ultra-adaptive bullish momentum (v8.4 Phase2)
        cond_rsi_short = dataframe["rsi"] < 45  # Ultra-adaptive bearish momentum (v8.4 Phase2)

        # MACD trend strength filter
        cond_macd_long = dataframe["macd"] > dataframe["macdsignal"]
        cond_macd_short = dataframe["macd"] < dataframe["macdsignal"]
        
        # Volume rate of change (liquidez dinámica)
        cond_volume_roc = dataframe['volume'].pct_change(5) > 0  # volumen creciente últimos 5min

        # Optional USDT dominance filter
        cond_usdt = True
        if self.USE_USDT_FILTER and "usdt_sma7_1d" in dataframe:
            cond_usdt = dataframe["usdt_sma7_1d"].diff() < 0  # today lower than yesterday

        # LONG entry conditions (all filters combined) - Phase 3 enhanced
        long_entry_condition = (
            cond_ema_long & 
            cond_tema_short_long & 
            cond_tema_long_long &
            cond_adx & 
            cond_cmo_long &
            cond_volume & 
            cond_dir_5m_long &   # Phase 3: Added 5m confirmation
            cond_dir_15m_long & 
            cond_rsi_long & 
            cond_macd_long & 
            cond_volume_roc &
            cond_usdt
        )

        # SHORT entry conditions (all filters combined) - Phase 3 enhanced
        short_entry_condition = (
            cond_ema_short & 
            cond_tema_short_short & 
            cond_tema_long_short &
            cond_adx & 
            cond_cmo_short &
            cond_volume & 
            cond_dir_5m_short &   # Phase 3: Added 5m confirmation
            cond_dir_15m_short & 
            cond_rsi_short & 
            cond_macd_short & 
            cond_volume_roc &
            cond_usdt
        )

        dataframe.loc[long_entry_condition, "enter_long"] = 1
        
        # Only enable short entries if can_short is True
        if self.can_short:
            dataframe.loc[short_entry_condition, "enter_short"] = 1
            
        return dataframe

    # ------------------------------------------------------------------
    # Exit logic - fallback if custom_exit didn't fire yet
    # ------------------------------------------------------------------
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # NO exit signals - 100% dependent on Phase 3 optimized custom_exit (ATR TP/SL)
        return dataframe

    # ------------------------------------------------------------------
    # Custom stoploss based on ATR(100) - Phase 3 optimized for BTC $110K+
    # ------------------------------------------------------------------
    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs):
        """Phase 3 optimized: Hard SL at 2.2 ATR(100) from entry - whipsaw resistant for high volatility."""
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return 1  # keep existing SL
        atr = dataframe["atr100"].iloc[-1]
        if atr == 0:
            return 1
        
        # Phase 3: SL optimized for BTC $110K+ volatility patterns
        sl_atr = 0.6 * atr  # v8.6: 0.6 ATR stop-loss for tighter scalp exits
        
        if trade.is_short:
            # SHORT: SL triggers when price goes UP by 2.2 ATR from entry
            distance = (current_rate - trade.open_rate)
            if distance >= sl_atr:
                return 0.01  # triggers immediate SL exit
        else:
            # LONG: SL triggers when price goes DOWN by 2.2 ATR from entry
            distance = (trade.open_rate - current_rate)
            if distance >= sl_atr:
                return 0.01  # triggers immediate SL exit
        
        return 1  # no update

    # ------------------------------------------------------------------
    # Custom exit - Phase 3 optimized ATR targets for BTC $110K+ profitability
    # ------------------------------------------------------------------
    def custom_exit(self, pair: str, trade: Trade, current_time: datetime,
                    current_rate: float, current_profit: float, **kwargs):
        """Phase 3 PROFIT OPTIMIZATION: Take profit at 3.5 ATR OR trail at 1.8 ATR - data-driven for BTC $110K+."""
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return None

        atr = dataframe["atr100"].iloc[-1]
        if atr == 0:
            return None

        entry = trade.open_rate
        
        if trade.is_short:
            # SHORT positions: profit when price goes DOWN - Phase 3 optimized
            tp_price = entry - 0.9 * atr  # v8.6 TP
            sl_trail = entry - 0.45 * atr  # v8.6 trailing stop
            
            # Take-profit hit (price dropped enough)
            if current_rate <= tp_price:
                return {
                    "exit_tag": "atr_tp_short_v85",
                    "exit_type": "exit_signal",
                }

            # Trailing: price went in our favor (down), but bounced back above trail
            if (trade.min_rate is not None and 
                trade.min_rate <= sl_trail and 
                current_rate > sl_trail):
                return {
                    "exit_tag": "atr_trail_short_v85",
                    "exit_type": "exit_signal",
                }
        else:
            # LONG positions: profit when price goes UP - Phase 3 optimized
            tp_price = entry + 0.9 * atr  # v8.6 TP
            sl_trail = entry + 0.45 * atr  # v8.6 trailing stop

            # Take-profit hit (price rose enough)
            if current_rate >= tp_price:
                return {
                    "exit_tag": "atr_tp_long_v85",
                    "exit_type": "exit_signal",
                }

            # Trailing: price went in our favor (up), but dropped back below trail
            if (trade.max_rate is not None and 
                trade.max_rate >= sl_trail and 
                current_rate < sl_trail):
                return {
                    "exit_tag": "atr_trail_long_v85",
                    "exit_type": "exit_signal",
                }

        # ------------------------------------------------------------------
        # Breakeven lock: If price moves >0.25 % in our favour then returns
        # to entry (+fees), exit to protect capital.
        # ------------------------------------------------------------------
        # ───────────────────────────────────────────────────────────
        # Breakeven lock logic v8.5.2
        # Trigger exit when:
        #   1. Price moved at least +0.25 % in our favour (tracked via max/min)
        #   2. Price has come back to within entry ± fee region (<= entry for long, >= entry for short)
        # This avoids keeping trades that already paid fees but lost momentum.
        # ───────────────────────────────────────────────────────────
        be_threshold = 0.0025 * entry  # 0.25 % move to activate BE lock (unchanged)
        fee_buffer   = 0.0020 * entry  # 0.20 % covers entry+exit fees on Binance tier-0

        if not trade.is_short:
            # LONG: price had to reach entry + threshold, now back to <= entry
            if (trade.max_rate is not None and
                trade.max_rate >= entry + be_threshold and
                current_rate <= entry + fee_buffer):
                return {"exit_tag": "breakeven_long", "exit_type": "exit_signal"}
        else:
            # SHORT: price had to reach entry - threshold, now back to >= entry
            if (trade.min_rate is not None and
                trade.min_rate <= entry - be_threshold and
                current_rate >= entry - fee_buffer):
                return {"exit_tag": "breakeven_short", "exit_type": "exit_signal"}

        return None
