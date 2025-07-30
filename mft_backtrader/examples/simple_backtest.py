"""
Simple Backtrader Backtest Example
==================================

This script demonstrates how to run a simple backtest using the Backtrader framework
with data converted from FreqTrade format.
"""
import backtrader as bt
import pandas as pd
import os
import sys
import logging

# Import our custom modules
from mft_backtrader.data.freqtrade_converter import FreqTradeConverter
from mft_backtrader.data.data_loader import BacktraderDataLoader
from mft_backtrader.strategies.scalping_strategy import ScalpingStrategy

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_backtest():
    """Run a simple backtest."""
    # Create a cerebro entity
    cerebro = bt.Cerebro()
    
    # Set up initial cash
    cerebro.broker.setcash(1000.0)
    
    # Set commission (0.1% per trade)
    cerebro.broker.setcommission(commission=0.001)
    
    # Set position size
    cerebro.addsizer(bt.sizers.PercentSizer, percents=10)  # 10% of portfolio per trade
    
    # Load data
    converter = FreqTradeConverter()
    loader = BacktraderDataLoader()
    
    # Try to load BTC/USDT 1m data
    data_file = "user_data/data/binance/BTC_USDT-1m.json"
    
    if os.path.exists(data_file):
        logger.info(f"Loading data from {data_file}")
        data_feed = loader.load_from_freqtrade_json(data_file, "BTC_USDT")
        cerebro.adddata(data_feed)
    else:
        logger.warning(f"Data file {data_file} not found. Creating sample data.")
        # Create sample data for demonstration
        import numpy as np
        from datetime import datetime, timedelta
        
        # Generate sample data
        dates = pd.date_range(datetime.now() - timedelta(days=7), periods=1000, freq='1min')
        prices = 100 + np.cumsum(np.random.randn(1000) * 0.1)
        df = pd.DataFrame({
            'open': prices,
            'high': prices + np.random.rand(1000) * 2,
            'low': prices - np.random.rand(1000) * 2,
            'close': prices + np.random.randn(1000) * 0.5,
            'volume': np.random.rand(1000) * 1000
        }, index=dates)
        
        data_feed = loader.load_from_dataframe(df, "SampleData")
        cerebro.adddata(data_feed)
    
    # Add strategy
    cerebro.addstrategy(ScalpingStrategy)
    
    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
    # Run over everything
    results = cerebro.run()
    
    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
    # Plot the result
    cerebro.plot()

if __name__ == "__main__":
    run_backtest()