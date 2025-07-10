# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file

"""
Multi-Horizon Momentum Strategy Extended with TEMA - v8.4 PHASE2
================================================================

PHASE 2 RECALIBRATED: Ultra-adaptive filters for BTC $110K+ conditions.
- 2025-optimized: ADX>38, RSI>55/45 for maximum market adaptability
- Scalping-optimized ATR targets: TP 2.5x, SL 1.5x, Trailing 1.2x  
- Ultra-fast entries/exits: Average trade duration <30 minutes
- Triple EMA + TEMA crossover + 2025-specific momentum filters
- 4h TEMA trend alignment prevents counter-trend trades
- Target: 20-30% win rate in 2025 BTC $110K+ market conditions

Strategy Components:
-------------------
1. **Original System**: Triple EMA (30/120/360) + RSI + MACD + Volume
2. **TEMA System**: TEMA(10/80) crossover + 4h TEMA(20/70) alignment
3. **Momentum Filters**: ADX > 40 + CMO thresholds for direction
4. **Risk Management**: Pure ATR-based exits (proven 47.2% win rate)

Entry Conditions (LONG):
-----------------------
- Triple EMA alignment (30 > 120 > 360)
- TEMA short-term uptrend (TEMA10 > TEMA80)  
- TEMA long-term uptrend (TEMA20_4h > TEMA70_4h)
- Strong momentum: ADX > 40 AND CMO > 40
- RSI > 60 (momentum confirmation)
- MACD bullish divergence
- Volume surge (2x average)
- 15m directional filter alignment

Entry Conditions (SHORT - optional):
-----------------------------------
- Triple EMA downtrend (30 < 120 < 360)
- TEMA short-term downtrend (TEMA10 < TEMA80)
- TEMA long-term downtrend (TEMA20_4h < TEMA70_4h)  
- Strong momentum: ADX > 40 AND CMO < -40
- RSI < 40 (bearish momentum)
- MACD bearish divergence
- Volume surge (2x average)
- 15m directional filter alignment

Risk Management:
---------------
- Stop Loss: 2.0 ATR below/above entry
- Take Profit: 3.5 ATR above/below entry  
- Trailing Stop: 1.5 ATR once in profit
- Emergency Stop: 30% hard floor

Back-test commands:
------------------
# With fees (realistic)
freqtrade backtesting -s MultiHorizonMomentum -p BTC/USDT,ETH/USDT --fee 0.1 --timeframe 1m

# Without fees (edge validation)  
freqtrade backtesting -s MultiHorizonMomentum -p BTC/USDT,ETH/USDT --fee 0 --timeframe 1m
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
    """Enhanced momentum strategy with TEMA trend-following and ATR exits."""

    INTERFACE_VERSION = 3
    timeframe: str = "1m"
    can_short: bool = False  # Set to True to enable short trading

    # Amount of history needed for indicators: max(360 for EMA, 100 for ATR, 80 for TEMA)
    startup_candle_count: int = 400

    # No static ROI - we exit via custom_exit / stoploss
    minimal_roi: Dict[str, float] = {}

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
        """Request 15m and 4h timeframes for directional filters.
        
        USDT dominance filter is disabled for 1m trading.
        """
        pairs: List[Tuple[str, str]] = []
        
        # Marco superior 15m para dirección
        if self.dp and self.dp.current_whitelist():
            for pair in self.dp.current_whitelist():
                pairs.append((pair, "15m"))
                pairs.append((pair, "4h"))  # For TEMA long-term trend
        
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

        # ATR for risk management
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

        # EMAs 15m para filtro direccional
        if self.dp and metadata:
            try:
                informative_15m = self.dp.get_pair_dataframe(pair=metadata["pair"], timeframe="15m")
                informative_15m["ema_fast_15m"] = ta.EMA(informative_15m, timeperiod=30)
                informative_15m["ema_mid_15m"] = ta.EMA(informative_15m, timeperiod=120)
                dataframe = merge_informative_pair(
                    dataframe, informative_15m, self.timeframe, "15m", ffill=True
                )
            except Exception:
                # En caso de que falten datos 15m
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
                    # En caso de que falten datos 4h
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

        # Filtro de liquidez ultra selectivo (solo trades premium) - v8.1 optimization
        cond_volume = dataframe['volume'] > dataframe['volume'].rolling(30).mean() * 3.0

        # Filtro direccional 15m (evita operar contra micro-tendencia)
        cond_dir_long = True  # Default en caso de que no haya datos 15m
        cond_dir_short = True
        if "ema_fast_15m_15m" in dataframe.columns and "ema_mid_15m_15m" in dataframe.columns:
            cond_dir_long = dataframe["ema_fast_15m_15m"] > dataframe["ema_mid_15m_15m"]
            cond_dir_short = dataframe["ema_fast_15m_15m"] < dataframe["ema_mid_15m_15m"]

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

        # LONG entry conditions (all filters combined)
        long_entry_condition = (
            cond_ema_long & 
            cond_tema_short_long & 
            cond_tema_long_long &
            cond_adx & 
            cond_cmo_long &
            cond_volume & 
            cond_dir_long & 
            cond_rsi_long & 
            cond_macd_long & 
            cond_volume_roc &
            cond_usdt
        )

        # SHORT entry conditions (all filters combined)
        short_entry_condition = (
            cond_ema_short & 
            cond_tema_short_short & 
            cond_tema_long_short &
            cond_adx & 
            cond_cmo_short &
            cond_volume & 
            cond_dir_short & 
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
        # ELIMINADOS TODOS LOS EXIT SIGNALS - 0% win rate en 1m scalping
        # 100% dependiente de custom_exit (ATR TP/SL) que tiene 47.2% win rate
        # NO hay exit signals - solo custom exit con ATR
        return dataframe

    # ------------------------------------------------------------------
    # Custom stoploss based on ATR(100) - supports both long and short
    # ------------------------------------------------------------------
    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs):
        """Hard SL at 1.5 ATR(100) from entry price - optimized for scalping."""
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return 1  # keep existing SL
        atr = dataframe["atr100"].iloc[-1]
        if atr == 0:
            return 1
        
        # SL dinámico a 1.5x ATR (optimizado para scalping rápido)
        sl_atr = 1.5 * atr
        
        if trade.is_short:
            # SHORT: SL triggers when price goes UP by 2 ATR from entry
            distance = (current_rate - trade.open_rate)
            if distance >= sl_atr:
                return 0.01  # triggers immediate SL exit
        else:
            # LONG: SL triggers when price goes DOWN by 2 ATR from entry
            distance = (trade.open_rate - current_rate)
            if distance >= sl_atr:
                return 0.01  # triggers immediate SL exit
        
        return 1  # no update

    # ------------------------------------------------------------------
    # Custom exit for ATR take-profit and trailing - supports long and short
    # ------------------------------------------------------------------
    def custom_exit(self, pair: str, trade: Trade, current_time: datetime,
                    current_rate: float, current_profit: float, **kwargs):
        """Scalping optimized: Take profit at 2.5 ATR(100) OR trail stop at 1.2 ATR once in profit."""
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return None

        atr = dataframe["atr100"].iloc[-1]
        if atr == 0:
            return None

        entry = trade.open_rate
        
        if trade.is_short:
            # SHORT positions: profit when price goes DOWN (scalping optimized)
            tp_price = entry - 2.5 * atr  # Take profit 2.5 ATR below entry (scalping)
            sl_trail = entry - 1.2 * atr  # Trailing stop 1.2 ATR below entry (scalping)
            
            # Take-profit hit (price dropped enough)
            if current_rate <= tp_price:
                return {
                    "exit_tag": "atr_tp_short",
                    "exit_type": "exit_signal",
                }

            # Trailing: price went in our favor (down), but bounced back above trail
            if (trade.min_rate is not None and 
                trade.min_rate <= sl_trail and 
                current_rate > sl_trail):
                return {
                    "exit_tag": "atr_trail_short",
                    "exit_type": "exit_signal",
                }
        else:
            # LONG positions: profit when price goes UP (scalping optimized)
            tp_price = entry + 2.5 * atr  # Take profit 2.5 ATR above entry (scalping)
            sl_trail = entry + 1.2 * atr  # Trailing stop 1.2 ATR above entry (scalping)

            # Take-profit hit (price rose enough)
            if current_rate >= tp_price:
                return {
                    "exit_tag": "atr_tp_long",
                    "exit_type": "exit_signal",
                }

            # Trailing: price went in our favor (up), but dropped back below trail
            if (trade.max_rate is not None and 
                trade.max_rate >= sl_trail and 
                current_rate < sl_trail):
                return {
                    "exit_tag": "atr_trail_long",
                    "exit_type": "exit_signal",
                }

        return None
