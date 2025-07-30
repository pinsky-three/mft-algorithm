"""
Backtrader Data Loader
======================

This module provides utilities to load data for Backtrader from various sources,
including converted FreqTrade data.
"""
import pandas as pd
import backtrader as bt
import os
from datetime import datetime
from typing import Dict, List, Optional, Union
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BacktraderDataLoader:
    """Load data for Backtrader from various sources."""
    
    def __init__(self):
        """Initialize the data loader."""
        pass
    
    def load_from_dataframe(self, df: pd.DataFrame, name: str = "Data") -> bt.feeds.PandasData:
        """
        Load data from a pandas DataFrame for Backtrader.
        
        Args:
            df (pd.DataFrame): DataFrame with datetime index and OHLCV data
            name (str): Name for the data feed
            
        Returns:
            bt.feeds.PandasData: Backtrader data feed
        """
        # Ensure the DataFrame has the required columns
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Create Backtrader data feed
        data_feed = bt.feeds.PandasData(
            dataname=df,
            name=name,
            timeframe=bt.TimeFrame.Minutes,  # Default to minutes, can be overridden
        )
        
        logger.info(f"Loaded data feed '{name}' with {len(df)} rows")
        return data_feed
    
    def load_from_csv(self, file_path: str, name: str = None) -> bt.feeds.PandasData:
        """
        Load data from a CSV file for Backtrader.
        
        Args:
            file_path (str): Path to the CSV file
            name (str): Name for the data feed (defaults to filename without extension)
            
        Returns:
            bt.feeds.PandasData: Backtrader data feed
        """
        if name is None:
            name = os.path.splitext(os.path.basename(file_path))[0]
        
        # Load CSV data
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        
        return self.load_from_dataframe(df, name)
    
    def load_from_freqtrade_json(self, file_path: str, name: str = None) -> bt.feeds.PandasData:
        """
        Load data directly from FreqTrade JSON format.
        
        Args:
            file_path (str): Path to the FreqTrade JSON file
            name (str): Name for the data feed (defaults to filename without extension)
            
        Returns:
            bt.feeds.PandasData: Backtrader data feed
        """
        if name is None:
            name = os.path.splitext(os.path.basename(file_path))[0]
        
        # Load JSON data
        df = pd.read_json(file_path)
        
        # Convert date column to datetime and set as index
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # Ensure column names are correct
        df.rename(columns={
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume'
        }, inplace=True)
        
        # Sort by date
        df.sort_index(inplace=True)
        
        return self.load_from_dataframe(df, name)
    
    def load_multiple_datafeeds(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, bt.feeds.PandasData]:
        """
        Load multiple data feeds from a dictionary of DataFrames.
        
        Args:
            data_dict (Dict[str, pd.DataFrame]): Dictionary mapping names to DataFrames
            
        Returns:
            Dict[str, bt.feeds.PandasData]: Dictionary mapping names to Backtrader data feeds
        """
        data_feeds = {}
        for name, df in data_dict.items():
            try:
                data_feeds[name] = self.load_from_dataframe(df, name)
            except Exception as e:
                logger.warning(f"Failed to load data feed '{name}': {str(e)}")
        
        return data_feeds

# Example usage
if __name__ == "__main__":
    # Example: Load data from CSV
    # loader = BacktraderDataLoader()
    # data_feed = loader.load_from_csv("data/BTC_USDT-1m.csv", "BTC_USDT")
    
    # Example: Load data from DataFrame
    # import numpy as np
    # dates = pd.date_range('2023-01-01', periods=100, freq='1min')
    # df = pd.DataFrame({
    #     'open': np.random.rand(100) * 100,
    #     'high': np.random.rand(100) * 100 + 10,
    #     'low': np.random.rand(100) * 100 - 10,
    #     'close': np.random.rand(100) * 100,
    #     'volume': np.random.rand(100) * 1000
    # }, index=dates)
    # data_feed = loader.load_from_dataframe(df, "SampleData")
    pass