"""
Base Strategy Class for Backtrader
==================================

This module provides a base strategy class that implements common functionality
used across different trading strategies.
"""
import backtrader as bt
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseStrategy(bt.Strategy):
    """
    Base strategy class with common functionality for trading strategies.
    
    This class provides:
    - Common indicators (EMA, RSI, MACD, ATR)
    - Market health calculations
    - Volume analysis
    - Trend detection
    - Utility methods for strategy development
    """
    
    params = (
        ('debug', False),  # Enable debug logging
    )
    
    def __init__(self):
        """Initialize the strategy."""
        self.orders = []  # Keep track of orders
        self.indicators = {}  # Store computed indicators
        self.log("BaseStrategy initialized")
    
    def log(self, txt: str, debug: bool = False):
        """
        Logging function for the strategy.
        
        Args:
            txt (str): Text to log
            debug (bool): Whether this is debug information
        """
        if debug and not self.p.debug:
            return
            
        dt = self.datas[0].datetime.date(0)
        tm = self.datas[0].datetime.time(0)
        logger.info(f'{dt} {tm}: {txt}')
    
    def compute_ema(self, data, period: int, name: str = None):
        """
        Compute EMA indicator.
        
        Args:
            data: Data series to compute EMA for
            period (int): EMA period
            name (str): Name for the indicator
            
        Returns:
            EMA indicator
        """
        if name is None:
            name = f"ema_{period}"
            
        ema = bt.indicators.EMA(data, period=period)
        self.indicators[name] = ema
        return ema
    
    def compute_rsi(self, data, period: int = 14, name: str = None):
        """
        Compute RSI indicator.
        
        Args:
            data: Data series to compute RSI for
            period (int): RSI period
            name (str): Name for the indicator
            
        Returns:
            RSI indicator
        """
        if name is None:
            name = f"rsi_{period}"
            
        rsi = bt.indicators.RSI(data, period=period)
        self.indicators[name] = rsi
        return rsi
    
    def compute_macd(self, data, fast: int = 12, slow: int = 26, signal: int = 9,
                     name: str = None) -> Dict[str, dict]:
        """
        Compute MACD indicator.
        
        Args:
            data: Data series to compute MACD for
            fast (int): Fast EMA period
            slow (int): Slow EMA period
            signal (int): Signal EMA period
            name (str): Base name for the indicator
            
        Returns:
            Dict[str, bt.indicators.MACD]: Dictionary with MACD components
        """
        if name is None:
            name = f"macd_{fast}_{slow}_{signal}"
            
        macd = bt.indicators.MACD(data, period_me1=fast, period_me2=slow, period_signal=signal)
        macd_dict = {
            f"{name}_macd": macd.macd,
            f"{name}_signal": macd.signal,
            f"{name}_histogram": macd.histogram
        }
        self.indicators.update(macd_dict)
        return macd_dict
    
    def compute_atr(self, data, period: int = 14, name: str = None):
        """
        Compute ATR indicator.
        
        Args:
            data: Data series to compute ATR for (expects OHLC data)
            period (int): ATR period
            name (str): Name for the indicator
            
        Returns:
            ATR indicator
        """
        if name is None:
            name = f"atr_{period}"
            
        # Assuming data is the first data feed with OHLC
        atr = bt.indicators.ATR(data, period=period)
        self.indicators[name] = atr
        return atr
    
    def compute_volume_sma(self, data, period: int = 20, name: str = None):
        """
        Compute SMA of volume.
        
        Args:
            data: Data series to compute volume SMA for
            period (int): SMA period
            name (str): Name for the indicator
            
        Returns:
            SMA of volume
        """
        if name is None:
            name = f"volume_sma_{period}"
            
        volume_sma = bt.indicators.SMA(data.volume, period=period)
        self.indicators[name] = volume_sma
        return volume_sma
    
    def compute_volume_ratio(self, data, period: int = 20, name: str = None):
        """
        Compute volume ratio (current volume / SMA of volume).
        
        Args:
            data: Data series to compute volume ratio for
            period (int): SMA period for volume
            name (str): Name for the indicator
            
        Returns:
            Volume ratio
        """
        if name is None:
            name = f"volume_ratio_{period}"
            
        volume_sma = self.compute_volume_sma(data, period, f"{name}_sma")
        volume_ratio = data.volume / volume_sma
        self.indicators[name] = volume_ratio
        return volume_ratio
    
    def compute_ema_alignment(self, ema_fast, ema_mid, ema_slow):
        """
        Compute EMA alignment (1 if fast > mid > slow, 0 otherwise).
        
        Args:
            ema_fast: Fast EMA indicator
            ema_mid: Mid EMA indicator
            ema_slow: Slow EMA indicator
            
        Returns:
            EMA alignment indicator (1 or 0)
        """
        ema_alignment = bt.And(
            ema_fast > ema_mid,
            ema_mid > ema_slow
        )
        ema_alignment = bt.If(ema_alignment, 1, 0)
        self.indicators['ema_alignment'] = ema_alignment
        return ema_alignment
    
    def compute_trend_strength(self, ema_alignment, period: int = 5):
        """
        Compute trend strength based on EMA alignment.
        
        Args:
            ema_alignment: EMA alignment indicator
            period (int): Period for SMA calculation
            
        Returns:
            Trend strength indicator
        """
        trend_strength = bt.indicators.SMA(ema_alignment, period=period)
        self.indicators['trend_strength'] = trend_strength
        return trend_strength
    
    def notify_order(self, order):
        """
        Notify when an order is submitted, accepted, or completed.
        
        Args:
            order: Order object
        """
        if order.status in [order.Submitted, order.Accepted]:
            # Order submitted/accepted - nothing to do yet
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f"BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}")
            elif order.issell():
                self.log(f"SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}")
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f"Order {order.Status[order.status]}")
        
        # Remove order from tracking list
        if order in self.orders:
            self.orders.remove(order)
    
    def notify_trade(self, trade):
        """
        Notify when a trade is opened or closed.
        
        Args:
            trade: Trade object
        """
        if not trade.isclosed:
            return
            
        self.log(f"OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}")
    
    def next(self):
        """
        Main strategy logic - called for each new bar.
        
        This method should be overridden by child classes.
        """
        pass
    
    def stop(self):
        """
        Called when the strategy is stopped.
        """
        self.log(f"Strategy stopped. Final portfolio value: {self.broker.getvalue():.2f}")

# Example usage
if __name__ == "__main__":
    # This is just for demonstration - not executable without Backtrader setup
    pass