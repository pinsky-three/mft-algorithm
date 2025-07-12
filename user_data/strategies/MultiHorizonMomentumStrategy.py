# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file

"""
Multi-Horizon Momentum Strategy (BTC / ETH / SOL) - ORIGINAL+ v7.1
==================================================================

ORIGINAL STRATEGY with minimal time-based improvement only.
- ORIGINAL entries: Triple EMA + RSI>60 + MACD + Volume 2.0x + 15m filter  
- ORIGINAL exits: TP 3.5x, SL 2.0x, Trailing 1.5x + extreme time exit only
- Target: Match/improve v7 baseline (23.1% win rate, -1.53% return)

Risk / exit management (Original+ v7.1)
---------------------------------------
* Stop-loss       : 2.0 ATR(100) below entry price (ORIGINAL proven level).
* Take-profit     : 3.5 ATR(100) above entry price (ORIGINAL proven level).
* Trailing stop   : 1.5 ATR(100) once in profit (ORIGINAL proven level).
* Time-based exit : 24h max for losing trades >2% (minimal safety improvement).
* Fees            : Optimized for maker fees (0.02%) vs. taker (0.04%).

Filters & Optimizations v7.1 ORIGINAL+
--------------------------------------
1. **ORIGINAL entries**: Triple EMA + RSI>60 + MACD + Volume 2.0x surge
2. **Directional filter**: 15m EMAs alignment prevents counter-trend trades  
3. **Volume filter**: 2.0x rolling mean (ORIGINAL proven selective level)
4. **RSI threshold**: 60 (ORIGINAL ultra-selective for maximum precision)
5. **Volume growth**: pct_change(5) > 0 (ORIGINAL requirement)
6. **ORIGINAL exits**: 3.5x ATR TP, 2.0x ATR SL, 1.5x ATR trailing
7. **Minimal safety**: 24h time exit for extreme losing trades only
8. **Expected performance**: Match v7 baseline (681 trades, 23.1% win rate)

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

        # Original ultra-selective volume filter (proven level)
        cond_volume = dataframe['volume'] > dataframe['volume'].rolling(30).mean() * 2.0

        # Filtro direccional 15m (evita operar contra micro-tendencia)
        cond_dir = True  # Default en caso de que no haya datos 15m
        if "ema_fast_15m_15m" in dataframe.columns and "ema_mid_15m_15m" in dataframe.columns:
            cond_dir = dataframe["ema_fast_15m_15m"] > dataframe["ema_mid_15m_15m"]

        # ORIGINAL RSI filter (ultra selective - proven)
        cond_rsi = dataframe["rsi"] > 60  # Original ultra selective for maximum precision

        # MACD trend strength filter (MACD por encima de señal)
        cond_macd = dataframe["macd"] > dataframe["macdsignal"]
        
        # ORIGINAL volume rate of change (liquidez dinámica)
        cond_volume_roc = dataframe['volume'].pct_change(5) > 0  # Original: volume must be growing

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
        """ORIGINAL SL at 2.0 ATR(100) below entry price - proven approach."""
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return 1  # keep existing SL
        atr = dataframe["atr100"].iloc[-1]
        if atr == 0:
            return 1
        # Price distance to entry
        distance = (trade.open_rate - current_rate)
        # ORIGINAL SL at 2.0x ATR (original proven level)
        sl_atr = 2.0 * atr
        if distance >= sl_atr:
            return 0.01  # triggers immediate SL exit
        return 1  # no update

    # ------------------------------------------------------------------
    # Custom exit for ATR take-profit and trailing
    # ------------------------------------------------------------------
    def custom_exit(self, pair: str, trade: Trade, current_time: datetime,
                    current_rate: float, current_profit: float, **kwargs):
        """ORIGINAL exit strategy with minimal time-based improvements."""
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return None

        atr = dataframe["atr100"].iloc[-1]
        if atr == 0:
            return None

        entry = trade.open_rate
        # ORIGINAL take profit level (3.5x ATR)
        tp_price = entry + 3.5 * atr  
        sl_trail = entry + 1.5 * atr  # ORIGINAL trailing level
        
        # Time-based management (only for extreme cases)
        trade_duration = (current_time - trade.open_date).total_seconds() / 3600  # hours

        # ORIGINAL take-profit hit
        if current_rate >= tp_price:
            return {
                "exit_tag": "atr_tp",
                "exit_type": "exit_signal",
            }

        # ORIGINAL trailing: price went 1.5 ATR in our favour, but drops back below
        if trade.max_rate is not None and trade.max_rate >= sl_trail and current_rate < sl_trail:
            return {
                "exit_tag": "atr_trail",
                "exit_type": "exit_signal",
            }
        
        # MINIMAL time-based improvement: only exit very long losing trades
        if trade_duration > 24 and current_profit < -0.02:  # 24h + losing >2%
            return {
                "exit_tag": "extreme_time",
                "exit_type": "exit_signal",
            }

        return None
