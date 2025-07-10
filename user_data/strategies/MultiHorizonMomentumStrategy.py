# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file

"""
Multi-Horizon Momentum Strategy (BTC / ETH / SOL) - Optimized v2
===============================================================

Optimized scalping strategy for 1m timeframe with fee-adjusted exits.
- Trades *long-only* on pairs with triple EMA alignment + directional filter
- Entry: EMA(30) > EMA(120) > EMA(360) on 1m + EMA trend on 15m
- Volume filter: 1.5x rolling mean (30 periods) for liquidity

Risk / exit management (Fee-optimized)
-------------------------------------
* Hard stop-loss  : 1 ATR(100) below entry price.
* Take-profit     : 3 ATR(100) above entry price (covers 0.2% fees).
* Trailing stop   : 1.5 ATR(100) once in profit.
* Exit orders     : Market stoploss for better execution.

Filters & Optimizations
----------------------
1. **Directional filter**: 15m EMAs (30/120) must align with 1m trend
2. **Volume filter**: 1.5x above 30-period rolling mean  
3. **ATR multipliers**: 3x/1.5x to overcome fee friction (0.1%+0.1%)
4. **Market SL**: Faster execution, avoids double fees on limit rejections

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

        # Filtro de liquidez (más restrictivo)
        cond_volume = dataframe['volume'] > dataframe['volume'].rolling(30).mean() * 1.5

        # Filtro direccional 15m (evita operar contra micro-tendencia)
        cond_dir = True  # Default en caso de que no haya datos 15m
        if "ema_fast_15m_15m" in dataframe.columns and "ema_mid_15m_15m" in dataframe.columns:
            cond_dir = dataframe["ema_fast_15m_15m"] > dataframe["ema_mid_15m_15m"]

        # Optional USDT dominance filter: 7‑day SMA trending **down**
        if self.USE_USDT_FILTER and "usdt_sma7_1d" in dataframe:
            cond_usdt = dataframe["usdt_sma7_1d"].diff() < 0  # today lower than yesterday
            entry_condition = cond_ema & cond_usdt & cond_volume & cond_dir
        else:
            entry_condition = cond_ema & cond_volume & cond_dir

        dataframe.loc[entry_condition, "enter_long"] = 1
        return dataframe

    # ------------------------------------------------------------------
    # Exit logic - fallback if custom_exit didn't fire yet
    # ------------------------------------------------------------------
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Exit when fast EMA crosses below mid EMA (momentum lost)
        exit_cond = qtpylib.crossed_below(dataframe["ema_fast"], dataframe["ema_mid"])
        dataframe.loc[exit_cond, "exit_long"] = 1
        return dataframe

    # ------------------------------------------------------------------
    # Custom stoploss based on ATR(14)
    # ------------------------------------------------------------------
    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs):
        """Hard SL at 1 ATR(100) below entry price."""
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return 1  # keep existing SL
        atr = dataframe["atr100"].iloc[-1]
        if atr == 0:
            return 1
        # Price distance to entry
        distance = (trade.open_rate - current_rate)
        # If price moved more than 1 ATR against us → exit at market
        if distance >= atr:
            return 0.01  # triggers immediate SL exit
        return 1  # no update

    # ------------------------------------------------------------------
    # Custom exit for ATR take-profit and trailing
    # ------------------------------------------------------------------
    def custom_exit(self, pair: str, trade: Trade, current_time: datetime,
                    current_rate: float, current_profit: float, **kwargs):
        """Take profit at 2 ATR(100) OR trail stop at 1 ATR once in profit."""
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return None

        atr = dataframe["atr100"].iloc[-1]
        if atr == 0:
            return None

        entry = trade.open_rate
        tp_price = entry + 3 * atr  # 3x ATR para cubrir fees
        sl_trail = entry + 1.5 * atr  # 1.5x ATR trailing

        # Take-profit hit
        if current_rate >= tp_price:
            return {
                "exit_tag": "atr_tp",
                "exit_type": "exit_signal",
            }

        # Trailing: price went 1 ATR in our favour, but drops back below SL trail
        if trade.max_rate is not None and trade.max_rate >= sl_trail and current_rate < sl_trail:
            return {
                "exit_tag": "atr_trail",
                "exit_type": "exit_signal",
            }

        return None
