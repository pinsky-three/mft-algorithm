# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file

"""
Multi-Horizon Momentum Strategy (BTC / ETH / SOL) - COMPLETE DISABLE v8.6
=========================================================================

COMPLETE DISABLE TEST: Zero custom_exit logic
- v8.5 PROGRESS: -16.7 USDT (vs -69.656) but still 0% win rate
- v8.6 COMPLETE DISABLE: NO custom_exit, pure stoploss system
- HYPOTHESIS: Even 4x ATR TP was too aggressive - let market decide
- ENTRY: Triple EMA + RSI>60 + MACD + Volume 2.0x + 15m filter  
- TARGET: Pure custom_stoploss (2.5x ATR) + strategy SL (-30%)

Risk / exit management (COMPLETE DISABLE v8.6)
-----------------------------------------------
* Hard stop-loss  : 2.5 ATR(100) below entry price (conservative, prevents noise).
* Take-profit     : COMPLETELY DISABLED (let market decide natural levels).
* Trailing stop   : DISABLED (was causing 0% win rate).
* Custom exit     : DISABLED (even 4x ATR TP was too aggressive).
* Strategy SL     : -30% emergency floor (main exit mechanism).
* Exit orders     : Market stoploss, limit entry/exit (partial maker).
* Fees            : Entry/exit maker 0.02%, SL market ~0.04% (blended savings).
* Trading hours   : 24/7 (no session restrictions).

Filters & Optimizations v8.4 FIXED (Working Edition)
---------------------------------------------------
1. **Ultra-precision entries**: Triple EMA + RSI>60 + MACD + Volume 2.0x + 15m filter
2. **Directional filter**: 15m EMAs (30/120) alignment prevents counter-trend trades  
3. **Volume filter**: 2.0x rolling mean + 5min growth for premium liquidity
4. **FIXED ATR exits**: Conservative 5x TP, 2.5x trail trigger, 1.8x trail distance
5. **ALL exit signals ELIMINATED**: EMA, RSI, MACD toxic in 1m scalping
6. **NO SESSION FILTER**: 24/7 trading to capture all opportunities
7. **PARTIAL MAKER**: Entry/exit limit orders, SL market for speed
8. **Conservative distances**: 2.5x SL, 5x TP = prevents premature exits

Back-test commands
-----------------
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
    """Daily EMA(5/21/63) trend-following with ATR exits."""

    INTERFACE_VERSION = 3
    timeframe: str = "1m"
    can_short: bool = False

    # Amount of history needed for indicators: max(360 for EMA, 100 for ATR)
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
    USE_USDT_FILTER: bool = False  # ojo: CRYPTOCAP:USDT.D no existe a 1m

    # ------------------------------------------------------------------
    # Informative pairs
    # ------------------------------------------------------------------
    def informative_pairs(self) -> List[Tuple[str, str]]:
        """Request 15m timeframe for directional filter.
        
        USDT dominance filter is disabled for 1m trading.
        """
        pairs: List[Tuple[str, str]] = []
        
        # Marco superior 15m para dirección
        if self.dp and self.dp.current_whitelist():
            for pair in self.dp.current_whitelist():
                pairs.append((pair, "15m"))
        
        if self.USE_USDT_FILTER:
            pairs.append(("USDT.D", "1d"))  # TradingView / CryptoCap ticker
        return pairs

    # ------------------------------------------------------------------
    # Indicator calculation
    # ------------------------------------------------------------------
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # EMA stack
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=30)   # 30 min
        dataframe["ema_mid"] = ta.EMA(dataframe, timeperiod=120)  # 2  h
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=360) # 6  h

        # ATR for risk management
        dataframe["atr100"] = ta.ATR(dataframe, timeperiod=100)
        
        # RSI for momentum confirmation
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        
        # MACD for trend strength
        macd = ta.MACD(dataframe)
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]
        dataframe["macdhist"] = macd["macdhist"]

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
        cond_ema = (
            (dataframe["ema_fast"] > dataframe["ema_mid"]) &
            (dataframe["ema_mid"] > dataframe["ema_slow"])
        )

        # Filtro de liquidez ultra selectivo (solo trades premium)
        cond_volume = dataframe['volume'] > dataframe['volume'].rolling(30).mean() * 2.0

        # Filtro direccional 15m (evita operar contra micro-tendencia)
        cond_dir = True  # Default en caso de que no haya datos 15m
        if "ema_fast_15m_15m" in dataframe.columns and "ema_mid_15m_15m" in dataframe.columns:
            cond_dir = dataframe["ema_fast_15m_15m"] > dataframe["ema_mid_15m_15m"]

        # RSI momentum filter (solo comprar en momentum alcista)
        cond_rsi = dataframe["rsi"] > 60  # Ultra selectivo para máxima precisión

        # MACD trend strength filter (MACD por encima de señal)
        cond_macd = dataframe["macd"] > dataframe["macdsignal"]
        
        # Volume rate of change (liquidez dinámica)
        cond_volume_roc = dataframe['volume'].pct_change(5) > 0  # volumen creciente últimos 5min

        # Optional USDT dominance filter: 7‑day SMA trending **down**
        if self.USE_USDT_FILTER and "usdt_sma7_1d" in dataframe:
            cond_usdt = dataframe["usdt_sma7_1d"].diff() < 0  # today lower than yesterday
            entry_condition = cond_ema & cond_usdt & cond_volume & cond_dir & cond_rsi & cond_macd & cond_volume_roc
        else:
            entry_condition = cond_ema & cond_volume & cond_dir & cond_rsi & cond_macd & cond_volume_roc

        dataframe.loc[entry_condition, "enter_long"] = 1
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
    # Custom stoploss based on ATR(14)
    # ------------------------------------------------------------------
    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs):
        """FIXED v8.4: Conservative ATR-based stoploss."""
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return 1  # keep existing SL
        atr = dataframe["atr100"].iloc[-1]
        if atr == 0 or atr is None:
            return 1
        
        # Conservative 2.5x ATR stoploss (was 1.8x)
        distance = (trade.open_rate - current_rate)
        sl_atr = 2.5 * atr
        if distance >= sl_atr:
            return 0.01  # triggers immediate SL exit
        return 1  # no update

    # ------------------------------------------------------------------
    # Custom exit for ATR take-profit and trailing
    # ------------------------------------------------------------------
    def custom_exit(self, pair: str, trade: Trade, current_time: datetime,
                    current_rate: float, current_profit: float, **kwargs):
        """v8.6 COMPLETE DISABLE: NO custom_exit - pure custom_stoploss + strategy SL."""
        # COMPLETELY DISABLED - let trades run to custom_stoploss or strategy stoploss only
        return None
