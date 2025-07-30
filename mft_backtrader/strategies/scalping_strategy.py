"""
Backtrader Scalping Strategy
============================

This strategy mirrors the CryptoScalpingOptimized strategy from FreqTrade
but implemented for Backtrader.
"""
import backtrader as bt
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
import logging

# Import the base strategy
from mft_backtrader.strategies.base_strategy import BaseStrategy

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScalpingStrategy(BaseStrategy):
    """
    Backtrader implementation of the CryptoScalpingOptimized strategy.
    
    This strategy implements:
    - EMA-based momentum detection
    - RSI filtering
    - MACD confirmation
    - Volume analysis
    - ATR-based volatility filtering
    - Market health assessment
    """
    
    params = (
        # Strategy parameters
        ('debug', False),
        
        # Timeframe parameters
        ('timeframe', '1m'),
        
        # EMA parameters
        ('ema_fast_period', 10),
        ('ema_mid_period', 21),
        ('ema_slow_period', 42),
        
        # RSI parameters
        ('rsi_period', 14),
        ('rsi_threshold', 55),
        
        # MACD parameters
        ('macd_fast', 12),
        ('macd_slow', 26),
        ('macd_signal', 9),
        
        # ATR parameters
        ('atr_period', 14),
        ('min_atr_ratio', 0.002),
        
        # Volume parameters
        ('volume_sma_period', 20),
        ('min_volume_ratio', 1.7),
        
        # Market health parameters
        ('min_market_health', 0.4),
        ('min_trend_quality', 0.18),
        ('max_choppiness', 0.75),
        
        # Momentum parameters
        ('momentum_strength', 0.75),
        
        # Stoploss and ROI
        ('stoploss', -0.025),
        ('roi_0', 0.030),
        ('roi_2', 0.025),
        ('roi_6', 0.020),
    )
    
    def __init__(self):
        """Initialize the strategy."""
        super().__init__()
        
        # Initialize indicators
        self.init_indicators()
        
        # Track position entry price for ROI calculation
        self.entry_price = None
        
        self.log("ScalpingStrategy initialized")
    
    def init_indicators(self):
        """Initialize all required indicators."""
        # EMA indicators
        self.ema_fast = self.compute_ema(self.data.close, self.p.ema_fast_period, 'ema_fast')
        self.ema_mid = self.compute_ema(self.data.close, self.p.ema_mid_period, 'ema_mid')
        self.ema_slow = self.compute_ema(self.data.close, self.p.ema_slow_period, 'ema_slow')
        
        # RSI indicator
        self.rsi = self.compute_rsi(self.data.close, self.p.rsi_period, 'rsi')
        
        # MACD indicator
        self.macd_components = self.compute_macd(
            self.data.close, 
            self.p.macd_fast, 
            self.p.macd_slow, 
            self.p.macd_signal,
            'macd'
        )
        self.macd = self.macd_components['macd_macd']
        self.macd_signal = self.macd_components['macd_signal']
        
        # ATR indicator
        self.atr = self.compute_atr(self.data, self.p.atr_period, 'atr')
        
        # Volume indicators
        self.volume_sma = self.compute_volume_sma(self.data, self.p.volume_sma_period, 'volume_sma')
        self.volume_ratio = self.compute_volume_ratio(self.data, self.p.volume_sma_period, 'volume_ratio')
        
        # EMA alignment and trend strength
        self.ema_alignment = self.compute_ema_alignment(self.ema_fast, self.ema_mid, self.ema_slow)
        self.trend_strength = self.compute_trend_strength(self.ema_alignment, 5)
        
        # Choppiness index (simplified)
        self.choppiness = bt.indicators.SMA(self.atr / (self.data.high - self.data.low), period=14) * 100
        self.choppy_market = self.choppiness > (self.p.max_choppiness * 100)
        
        # Market health score (simplified)
        self.market_health = (bt.If(~self.choppy_market, 1, 0) + 
                             bt.If(self.trend_strength >= self.p.min_trend_quality, 1, 0) + 
                             bt.If(self.volume_ratio > 1.2, 1, 0) + 
                             bt.If(self.atr / self.data.close > 0.0015, 1, 0)) / 4
        
        # Volatility regime
        self.atr_sma = bt.indicators.SMA(self.atr, period=20)
        self.volatility_ratio = self.atr / self.atr_sma
        self.favorable_volatility = bt.And(
            self.volatility_ratio > 1.1,
            self.volatility_ratio < 2.5
        )
        
        # Trend strength regime
        self.ema_spread = (self.ema_fast - self.ema_slow) / self.data.close
        self.trend_strength_alt = bt.Abs(self.ema_spread)
        self.trending_regime = self.trend_strength_alt > 0.002
        
        # Regime favorable
        self.regime_favorable = bt.And(
            self.favorable_volatility,
            self.trending_regime,
            self.market_health >= self.p.min_market_health,
            self.trend_strength >= self.p.min_trend_quality,
            ~self.choppy_market
        )
        
        # Momentum strength
        momentum_conditions = [
            self.ema_fast > self.ema_mid,
            self.ema_mid > self.ema_slow,
            self.rsi > self.p.rsi_threshold,
            self.macd > self.macd_signal,
            self.data.close > self.ema_fast
        ]
        
        # Count how many momentum conditions are met
        momentum_sum = sum(momentum_conditions)
        self.momentum_strength_calc = momentum_sum / len(momentum_conditions)
        self.momentum_aligned = self.momentum_strength_calc >= self.p.momentum_strength
        
        # Volume confirmed
        self.volume_confirmed = self.volume_ratio > self.p.min_volume_ratio
        
        # Volatile enough
        self.volatile_enough = (self.atr / self.data.close) > self.p.min_atr_ratio
    
    def next(self):
        """Main strategy logic."""
        # Skip if we don't have enough data
        if len(self) < self.p.ema_slow_period:
            return
        
        # Check if we have an open position
        if self.position:
            self.manage_open_position()
        else:
            self.look_for_entry()
    
    def look_for_entry(self):
        """Look for entry opportunities."""
        # Check all entry conditions
        momentum_ok = self.momentum_aligned[0]
        volume_ok = self.volume_confirmed[0]
        volatility_ok = self.volatile_enough[0]
        regime_ok = self.regime_favorable[0]
        
        # Additional conditions for entry
        green_candle = self.data.close[0] > self.data.open[0]
        rsi_ok = 58 < self.rsi[0] < 85
        market_health_ok = self.market_health[0] >= 0.5
        
        # Entry condition
        entry_condition = (
            momentum_ok and 
            volume_ok and 
            volatility_ok and 
            regime_ok and 
            green_candle and 
            rsi_ok and 
            market_health_ok
        )
        
        if entry_condition:
            # Calculate position size (simple fixed size for now)
            size = self.broker.getcash() / self.data.close[0] * 0.1  # 10% of available cash
            
            # Place buy order
            self.buy(size=size)
            self.entry_price = self.data.close[0]
            self.log(f"BUY CREATE, Price: {self.data.close[0]:.2f}, Size: {size:.4f}")
    
    def manage_open_position(self):
        """Manage an open position."""
        # Check for stoploss
        if self.position:
            price_change = (self.data.close[0] - self.entry_price) / self.entry_price
            if price_change <= self.p.stoploss:
                self.sell(size=self.position.size)
                self.log(f"STOPLOSS HIT, Price: {self.data.close[0]:.2f}")
                return
        
        # Check for ROI exit
        if self.position and self.entry_price:
            price_change = (self.data.close[0] - self.entry_price) / self.entry_price
            
            # ROI ladder logic
            bars_held = len(self) - self.bar_executed if hasattr(self, 'bar_executed') else 0
            
            if bars_held >= 6 and price_change >= self.p.roi_6:
                self.sell(size=self.position.size)
                self.log(f"ROI EXIT (6+ bars), Price: {self.data.close[0]:.2f}")
                return
            elif bars_held >= 2 and price_change >= self.p.roi_2:
                self.sell(size=self.position.size)
                self.log(f"ROI EXIT (2+ bars), Price: {self.data.close[0]:.2f}")
                return
            elif price_change >= self.p.roi_0:
                self.sell(size=self.position.size)
                self.log(f"ROI EXIT (immediate), Price: {self.data.close[0]:.2f}")
                return

# Example usage
if __name__ == "__main__":
    # This is just for demonstration - not executable without Backtrader setup
    pass