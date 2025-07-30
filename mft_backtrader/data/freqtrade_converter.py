"""
FreqTrade to Backtrader Data Converter
=====================================

This module provides utilities to convert FreqTrade JSON data format to Backtrader compatible format.
"""
import json
import pandas as pd
import numpy as np
from datetime import datetime
import os
from typing import Dict, List, Optional, Union
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FreqTradeConverter:
    """Convert FreqTrade JSON data to Backtrader compatible format."""
    
    def __init__(self):
        """Initialize the converter."""
        pass
    
    def load_freqtrade_data(self, file_path: str) -> pd.DataFrame:
        """
        Load FreqTrade JSON data and convert to pandas DataFrame.
        
        Args:
            file_path (str): Path to the FreqTrade JSON file
            
        Returns:
            pd.DataFrame: DataFrame with datetime index and OHLCV data
        """
        try:
            # Load JSON data
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Convert date strings to datetime
            df['date'] = pd.to_datetime(df['date'])
            
            # Set datetime as index
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
            
            # Ensure data types
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            logger.info(f"Loaded data from {file_path}: {len(df)} rows")
            return df
            
        except Exception as e:
            logger.error(f"Error loading data from {file_path}: {str(e)}")
            raise
    
    def convert_single_pair(self, file_path: str) -> pd.DataFrame:
        """
        Convert a single pair's data to Backtrader format.
        
        Args:
            file_path (str): Path to the FreqTrade JSON file
            
        Returns:
            pd.DataFrame: Backtrader compatible DataFrame
        """
        return self.load_freqtrade_data(file_path)
    
    def convert_multiple_pairs(self, directory_path: str, pair_filter: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        """
        Convert multiple pairs' data to Backtrader format.
        
        Args:
            directory_path (str): Path to directory containing FreqTrade JSON files
            pair_filter (List[str], optional): List of pairs to convert (e.g., ['BTC_USDT', 'ETH_USDT'])
            
        Returns:
            Dict[str, pd.DataFrame]: Dictionary mapping pair names to DataFrames
        """
        data_dict = {}
        
        # List all JSON files in directory
        for filename in os.listdir(directory_path):
            if filename.endswith('.json'):
                # Extract pair and timeframe from filename
                # Expected format: PAIR-TIMEFRAME.json (e.g., BTC_USDT-1m.json)
                pair_timeframe = filename.replace('.json', '')
                if '-' in pair_timeframe:
                    pair = pair_timeframe.split('-')[0]
                else:
                    pair = pair_timeframe
                
                # Apply pair filter if provided
                if pair_filter and pair not in pair_filter:
                    continue
                
                file_path = os.path.join(directory_path, filename)
                try:
                    data_dict[pair_timeframe] = self.load_freqtrade_data(file_path)
                    logger.info(f"Converted {filename}")
                except Exception as e:
                    logger.warning(f"Failed to convert {filename}: {str(e)}")
        
        return data_dict
    
    def save_backtrader_data(self, df: pd.DataFrame, output_path: str) -> None:
        """
        Save DataFrame in a Backtrader compatible format.
        
        Args:
            df (pd.DataFrame): DataFrame to save
            output_path (str): Path to save the data
        """
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save as CSV (Backtrader can read CSV)
        df.to_csv(output_path)
        logger.info(f"Saved Backtrader data to {output_path}")

# Example usage
if __name__ == "__main__":
    converter = FreqTradeConverter()
    
    # Example: Convert a single file
    # df = converter.convert_single_pair("user_data/data/binance/BTC_USDT-1m.json")
    # print(df.head())
    
    # Example: Convert multiple files
    # data_dict = converter.convert_multiple_pairs("user_data/data/binance/")
    # for pair, df in data_dict.items():
    #     print(f"{pair}: {len(df)} rows")