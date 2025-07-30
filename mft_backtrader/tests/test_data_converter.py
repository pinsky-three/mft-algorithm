"""
Tests for the FreqTrade to Backtrader Data Converter
====================================================

This module contains tests for the FreqTradeConverter class.
"""
import unittest
import pandas as pd
import numpy as np
import os
import tempfile
import json
from datetime import datetime, timedelta

# Import the module to test
from backtrader.data.freqtrade_converter import FreqTradeConverter

class TestFreqTradeConverter(unittest.TestCase):
    """Test cases for the FreqTradeConverter class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.converter = FreqTradeConverter()
        
        # Create sample FreqTrade data
        self.sample_data = [
            {
                "date": "2023-01-01 00:00:00",
                "open": 100.0,
                "high": 110.0,
                "low": 90.0,
                "close": 105.0,
                "volume": 1000.0
            },
            {
                "date": "2023-01-01 00:01:00",
                "open": 105.0,
                "high": 115.0,
                "low": 95.0,
                "close": 110.0,
                "volume": 1100.0
            },
            {
                "date": "2023-01-01 00:02:00",
                "open": 110.0,
                "high": 120.0,
                "low": 100.0,
                "close": 115.0,
                "volume": 1200.0
            }
        ]
        
        # Create a temporary file with sample data
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(self.sample_data, self.temp_file)
        self.temp_file.close()
    
    def tearDown(self):
        """Clean up test fixtures after each test method."""
        # Remove temporary file
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_load_freqtrade_data(self):
        """Test loading FreqTrade JSON data."""
        # Load data
        df = self.converter.load_freqtrade_data(self.temp_file.name)
        
        # Check that we have the right number of rows
        self.assertEqual(len(df), 3)
        
        # Check column names
        expected_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in expected_columns:
            self.assertIn(col, df.columns)
        
        # Check data types
        for col in expected_columns:
            self.assertTrue(pd.api.types.is_numeric_dtype(df[col]))
        
        # Check index type
        self.assertTrue(isinstance(df.index, pd.DatetimeIndex))
        
        # Check specific values
        self.assertEqual(df.iloc[0]['open'], 100.0)
        self.assertEqual(df.iloc[0]['close'], 105.0)
        self.assertEqual(df.iloc[1]['volume'], 1100.0)
    
    def test_convert_single_pair(self):
        """Test converting a single pair's data."""
        df = self.converter.convert_single_pair(self.temp_file.name)
        
        # Basic checks (should be same as load_freqtrade_data)
        self.assertEqual(len(df), 3)
        self.assertIn('open', df.columns)
        self.assertIn('close', df.columns)
        self.assertIn('volume', df.columns)
    
    def test_convert_multiple_pairs(self):
        """Test converting multiple pairs' data."""
        # Create a temporary directory with multiple files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple sample files
            pairs = ['BTC_USDT', 'ETH_USDT', 'SOL_USDT']
            for pair in pairs:
                file_path = os.path.join(temp_dir, f"{pair}-1m.json")
                with open(file_path, 'w') as f:
                    json.dump(self.sample_data, f)
            
            # Convert multiple pairs
            data_dict = self.converter.convert_multiple_pairs(temp_dir)
            
            # Check results
            self.assertEqual(len(data_dict), 3)
            for pair in pairs:
                key = f"{pair}-1m"
                self.assertIn(key, data_dict)
                self.assertEqual(len(data_dict[key]), 3)
    
    def test_convert_multiple_pairs_with_filter(self):
        """Test converting multiple pairs with a filter."""
        # Create a temporary directory with multiple files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple sample files
            pairs = ['BTC_USDT', 'ETH_USDT', 'SOL_USDT']
            for pair in pairs:
                file_path = os.path.join(temp_dir, f"{pair}-1m.json")
                with open(file_path, 'w') as f:
                    json.dump(self.sample_data, f)
            
            # Convert with filter
            data_dict = self.converter.convert_multiple_pairs(temp_dir, ['BTC_USDT', 'ETH_USDT'])
            
            # Check results (should only have 2 pairs)
            self.assertEqual(len(data_dict), 2)
            self.assertIn('BTC_USDT-1m', data_dict)
            self.assertIn('ETH_USDT-1m', data_dict)
            self.assertNotIn('SOL_USDT-1m', data_dict)

class TestDataLoader(unittest.TestCase):
    """Test cases for the BacktraderDataLoader class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Import here to avoid circular imports
        from backtrader.data.data_loader import BacktraderDataLoader
        self.loader = BacktraderDataLoader()
        
        # Create sample DataFrame
        dates = pd.date_range('2023-01-01', periods=3, freq='1min')
        self.sample_df = pd.DataFrame({
            'open': [100.0, 105.0, 110.0],
            'high': [110.0, 115.0, 120.0],
            'low': [90.0, 95.0, 100.0],
            'close': [105.0, 110.0, 115.0],
            'volume': [1000.0, 1100.0, 1200.0]
        }, index=dates)
        
        # Create a temporary CSV file
        self.temp_csv = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        self.sample_df.to_csv(self.temp_csv.name)
        self.temp_csv.close()
    
    def tearDown(self):
        """Clean up test fixtures after each test method."""
        # Remove temporary file
        if os.path.exists(self.temp_csv.name):
            os.unlink(self.temp_csv.name)
    
    def test_load_from_dataframe(self):
        """Test loading data from a DataFrame."""
        # This test would require backtrader to be fully installed
        # For now, we'll just check that the method exists and doesn't crash
        try:
            # Import backtrader
            import backtrader as bt
            data_feed = self.loader.load_from_dataframe(self.sample_df, "Test")
            self.assertIsNotNone(data_feed)
        except ImportError:
            # Skip test if backtrader is not available
            self.skipTest("Backtrader not available")
    
    def test_load_from_csv(self):
        """Test loading data from a CSV file."""
        try:
            # Import backtrader
            import backtrader as bt
            data_feed = self.loader.load_from_csv(self.temp_csv.name, "Test")
            self.assertIsNotNone(data_feed)
        except ImportError:
            # Skip test if backtrader is not available
            self.skipTest("Backtrader not available")

if __name__ == '__main__':
    unittest.main()