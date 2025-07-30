"""
Tests for the Base Strategy Class
=================================

This module contains tests for the BaseStrategy class.
"""
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Mock backtrader for testing
class MockData:
    def __init__(self):
        self.open = MockLine()
        self.high = MockLine()
        self.low = MockLine()
        self.close = MockLine()
        self.volume = MockLine()

class MockLine:
    def __init__(self):
        self._data = []
    
    def __getitem__(self, key):
        if isinstance(key, int):
            # Return a single value
            if key == 0:
                return 100.0  # Current value
            else:
                # For negative indices, return past values
                return 100.0 + key
        return self
    
    def __gt__(self, other):
        return MockCondition(True)
    
    def __lt__(self, other):
        return MockCondition(True)
    
    def __eq__(self, other):
        return MockCondition(True)

class MockCondition:
    def __init__(self, value):
        self.value = value
    
    def __and__(self, other):
        return MockCondition(self.value and other.value)
    
    def __or__(self, other):
        return MockCondition(self.value or other.value)

class MockIndicator:
    def __init__(self, data=None, period=None):
        self.data = data
        self.period = period
        self._data = [100.0] * 100  # Mock data
    
    def __getitem__(self, key):
        return 100.0

# Mock backtrader module
import sys
from unittest.mock import MagicMock

# Create a mock backtrader module
mock_bt = MagicMock()
mock_bt.indicators.EMA = MockIndicator
mock_bt.indicators.RSI = MockIndicator
mock_bt.indicators.MACD = MockIndicator
mock_bt.indicators.ATR = MockIndicator
mock_bt.indicators.SMA = MockIndicator
mock_bt.And = lambda *args: MockCondition(True)
mock_bt.If = lambda condition, true_val, false_val: true_val
mock_bt.Strategy = MagicMock()

# Add the mock to sys.modules
sys.modules['backtrader'] = mock_bt

# Now we can import our strategy
from backtrader.strategies.base_strategy import BaseStrategy

class TestBaseStrategy(unittest.TestCase):
    """Test cases for the BaseStrategy class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a mock strategy instance
        self.strategy = BaseStrategy()
        
        # Mock the data
        self.strategy.datas = [MockData()]
        
        # Mock broker
        self.strategy.broker = MagicMock()
        self.strategy.broker.getcash.return_value = 1000.0
        
        # Mock orders list
        self.strategy.orders = []
        
        # Mock indicators dict
        self.strategy.indicators = {}
    
    def test_initialization(self):
        """Test strategy initialization."""
        # Check that orders list is initialized
        self.assertEqual(self.strategy.orders, [])
        
        # Check that indicators dict is initialized
        self.assertEqual(self.strategy.indicators, {})
    
    def test_log(self):
        """Test the log method."""
        # This should not raise an exception
        self.strategy.log("Test message")
        
        # Test debug logging (should not print when debug is False)
        self.strategy.log("Debug message", debug=True)
    
    def test_compute_ema(self):
        """Test EMA computation."""
        mock_data = MockData()
        ema = self.strategy.compute_ema(mock_data.close, 10, 'test_ema')
        
        # Check that the indicator was stored
        self.assertIn('test_ema', self.strategy.indicators)
    
    def test_compute_rsi(self):
        """Test RSI computation."""
        mock_data = MockData()
        rsi = self.strategy.compute_rsi(mock_data.close, 14, 'test_rsi')
        
        # Check that the indicator was stored
        self.assertIn('test_rsi', self.strategy.indicators)
    
    def test_compute_macd(self):
        """Test MACD computation."""
        mock_data = MockData()
        macd_dict = self.strategy.compute_macd(mock_data.close, 12, 26, 9, 'test_macd')
        
        # Check that the indicators were stored
        expected_keys = ['test_macd_macd', 'test_macd_signal', 'test_macd_histogram']
        for key in expected_keys:
            self.assertIn(key, self.strategy.indicators)
    
    def test_compute_atr(self):
        """Test ATR computation."""
        mock_data = MockData()
        atr = self.strategy.compute_atr(mock_data, 14, 'test_atr')
        
        # Check that the indicator was stored
        self.assertIn('test_atr', self.strategy.indicators)
    
    def test_compute_volume_sma(self):
        """Test volume SMA computation."""
        mock_data = MockData()
        volume_sma = self.strategy.compute_volume_sma(mock_data, 20, 'test_volume_sma')
        
        # Check that the indicator was stored
        self.assertIn('test_volume_sma', self.strategy.indicators)
    
    def test_compute_volume_ratio(self):
        """Test volume ratio computation."""
        mock_data = MockData()
        volume_ratio = self.strategy.compute_volume_ratio(mock_data, 20, 'test_volume_ratio')
        
        # Check that the indicator was stored
        self.assertIn('test_volume_ratio', self.strategy.indicators)
    
    def test_compute_ema_alignment(self):
        """Test EMA alignment computation."""
        ema_fast = MockIndicator()
        ema_mid = MockIndicator()
        ema_slow = MockIndicator()
        
        ema_alignment = self.strategy.compute_ema_alignment(ema_fast, ema_mid, ema_slow)
        
        # Check that the indicator was stored
        self.assertIn('ema_alignment', self.strategy.indicators)
    
    def test_compute_trend_strength(self):
        """Test trend strength computation."""
        ema_alignment = MockIndicator()
        trend_strength = self.strategy.compute_trend_strength(ema_alignment, 5)
        
        # Check that the indicator was stored
        self.assertIn('trend_strength', self.strategy.indicators)
    
    def test_notify_order(self):
        """Test order notification."""
        # Create a mock order
        mock_order = MagicMock()
        mock_order.status = 2  # Completed
        mock_order.isbuy.return_value = True
        mock_order.issell.return_value = False
        mock_order.executed.price = 100.0
        mock_order.executed.value = 1000.0
        mock_order.executed.comm = 1.0
        
        # Add order to tracking list
        self.strategy.orders.append(mock_order)
        
        # This should not raise an exception
        self.strategy.notify_order(mock_order)
        
        # Check that order was removed from tracking list
        self.assertNotIn(mock_order, self.strategy.orders)
    
    def test_notify_trade(self):
        """Test trade notification."""
        # Create a mock trade
        mock_trade = MagicMock()
        mock_trade.isclosed = True
        mock_trade.pnl = 10.0
        mock_trade.pnlcomm = 9.0
        
        # This should not raise an exception
        self.strategy.notify_trade(mock_trade)

if __name__ == '__main__':
    unittest.main()