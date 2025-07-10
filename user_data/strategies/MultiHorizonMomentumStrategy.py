# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file

"""
Multi-Horizon Momentum Strategy (BTC / ETH / SOL)
=================================================

Port of the daily EMA-stack + ATR risk-layer described in the chat.
- Trades *long-only* on pairs that meet the condition::
    EMA(5) > EMA(21) > EMA(63)
  **and** USDT dominance (7-day SMA) is *falling* (optional filter).

Risk / exit management
----------------------
* Hard stop-loss  : 1 ATR(14) below entry price.
* Take-profit     : 2 ATR(14) above entry price.
* Trailing stop   : handled by custom_exit once in profit.

Notes
-----
1. Timeframe is **1d** to imitate the daily rebalance in the spec.
2. If your exchange does **not** provide a symbol for USDT dominance
   ("CRYPTOCAP:USDT.D" on TradingView, for example) comment-out the
   informative-pair section and set ``USE_USDT_FILTER = False``.
3. Back-test on Binance futures example command::
       freqtrade backtesting -s multi_horizon_momentum \
         -p BTC/USDT,ETH/USDT,SOL/USDT --timeframe 1d
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
    timeframe: str = "1d"
    can_short: bool = False

    # Amount of history needed for indicators: max(63 for EMA, 14 for ATR)
    startup_candle_count: int = 100

    # No static ROI - we exit via custom_exit / stoploss
    minimal_roi: Dict[str, float] = {}

    # Emergency stoploss (will rarely trigger thanks to ATR SL in custom_exit)
    stoploss: float = -0.30  # 30% hard floor

    # Trailing handled by custom_exit - keep disabled here
    trailing_stop = False

    # ---------------------------------------------------------------------
    # Configuration flags
    # ---------------------------------------------------------------------
    USE_USDT_FILTER: bool = False  # set to False if no USDT dominance data

    # ------------------------------------------------------------------
    # Informative pairs
    # ------------------------------------------------------------------
    def informative_pairs(self) -> List[Tuple[str, str]]:
        """Request USDT dominance daily candles as an informative pair.

        Works if your DataProvider is able to fetch the symbol
        e.g. "CRYPTOCAP:USDT.D" via the *TradingView* exchange plugin.
        """
        pairs: List[Tuple[str, str]] = []
        if self.USE_USDT_FILTER:
            pairs.append(("USDT.D", "1d"))  # TradingView / CryptoCap ticker
        return pairs

    # ------------------------------------------------------------------
    # Indicator calculation
    # ------------------------------------------------------------------
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # EMA stack
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=5)
        dataframe["ema_mid"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=63)

        # ATR for risk management
        dataframe["atr14"] = ta.ATR(dataframe, timeperiod=14)

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

        # Optional USDT dominance filter: 7‑day SMA trending **down**
        if self.USE_USDT_FILTER and "usdt_sma7_1d" in dataframe:
            cond_usdt = dataframe["usdt_sma7_1d"].diff() < 0  # today lower than yesterday
            entry_condition = cond_ema & cond_usdt
        else:
            entry_condition = cond_ema

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
        """Hard SL at 1 ATR(14) below entry price."""
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return 1  # keep existing SL
        atr = dataframe["atr14"].iloc[-1]
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
        """Take profit at 2 ATR(14) OR trail stop at 1 ATR once in profit."""
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return None

        atr = dataframe["atr14"].iloc[-1]
        if atr == 0:
            return None

        entry = trade.open_rate
        tp_price = entry + 2 * atr
        sl_trail = entry + atr  # move SL to breakeven +1 ATR once hit

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
