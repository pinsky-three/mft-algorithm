"""
Backtrader Parameter Optimization Example
========================================

This script demonstrates how to optimize strategy parameters using Backtrader's
optimization capabilities.
"""
import backtrader as bt
import pandas as pd
import os
import sys
import logging
import numpy as np
from datetime import datetime, timedelta

# Import our custom modules
from mft_backtrader.data.freqtrade_converter import FreqTradeConverter
from mft_backtrader.data.data_loader import BacktraderDataLoader
from mft_backtrader.strategies.scalping_strategy import ScalpingStrategy

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_optimization():
    """Run parameter optimization for the scalping strategy."""
    # Create sample data for demonstration
    dates = pd.date_range(datetime.now() - timedelta(days=7), periods=1000, freq='1min')
    prices = 100 + np.cumsum(np.random.randn(1000) * 0.1)
    df = pd.DataFrame({
        'open': prices,
        'high': prices + np.random.rand(1000) * 2,
        'low': prices - np.random.rand(1000) * 2,
        'close': prices + np.random.randn(1000) * 0.5,
        'volume': np.random.rand(1000) * 1000
    }, index=dates)
    
    # Create a cerebro entity
    cerebro = bt.Cerebro()
    
    # Set up initial cash
    cerebro.broker.setcash(1000.0)
    
    # Set commission (0.1% per trade)
    cerebro.broker.setcommission(commission=0.001)
    
    # Load data
    loader = BacktraderDataLoader()
    data_feed = loader.load_from_dataframe(df, "SampleData")
    cerebro.adddata(data_feed)
    
    # Add strategy with parameter ranges for optimization
    cerebro.optstrategy(
        ScalpingStrategy,
        ema_fast_period=range(8, 16),
        ema_mid_period=range(18, 26),
        rsi_threshold=range(50, 60)
    )
    
    # Run optimization
    logger.info("Starting parameter optimization...")
    results = cerebro.run()
    
    # Analyze results
    final_results = []
    for result in results:
        strat = result[0]
        final_results.append({
            'ema_fast_period': strat.params.ema_fast_period,
            'ema_mid_period': strat.params.ema_mid_period,
            'rsi_threshold': strat.params.rsi_threshold,
            'final_value': cerebro.broker.getvalue(),
            'return_pct': (cerebro.broker.getvalue() - 1000.0) / 1000.0 * 100
        })
    
    # Sort by return
    final_results.sort(key=lambda x: x['return_pct'], reverse=True)
    
    # Print top 5 results
    print("\n=== Top 5 Parameter Combinations ===")
    for i, result in enumerate(final_results[:5]):
        print(f"{i+1}. EMA Fast: {result['ema_fast_period']}, "
              f"EMA Mid: {result['ema_mid_period']}, "
              f"RSI Threshold: {result['rsi_threshold']}, "
              f"Return: {result['return_pct']:.2f}%")

if __name__ == "__main__":
    run_optimization()