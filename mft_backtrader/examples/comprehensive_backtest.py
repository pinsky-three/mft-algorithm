"""
Comprehensive Backtrader Backtest Example
========================================

This script demonstrates how to run a comprehensive backtest with multiple strategies,
multiple pairs, and detailed analysis.
"""
import backtrader as bt
import pandas as pd
import os
import sys
import logging
import json
from datetime import datetime
from typing import Dict, List

# Import our custom modules
from mft_backtrader.data.freqtrade_converter import FreqTradeConverter
from mft_backtrader.data.data_loader import BacktraderDataLoader
from mft_backtrader.strategies.scalping_strategy import ScalpingStrategy
from mft_backtrader.strategies.scalping_july_strategy import ScalpingJulyStrategy

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BacktestAnalyzer:
    """Analyze backtest results."""
    
    def __init__(self):
        pass
    
    def analyze_results(self, cerebro, results, strategy_name: str = "Strategy"):
        """
        Analyze backtest results.
        
        Args:
            cerebro: Backtrader cerebro instance
            results: Backtest results
            strategy_name (str): Name of the strategy
        """
        # Get the strategy instance
        strat = results[0]
        
        # Calculate performance metrics
        start_value = cerebro.broker.startingcash
        end_value = cerebro.broker.getvalue()
        total_return = (end_value - start_value) / start_value * 100
        
        # Print results
        print(f"\n=== {strategy_name} Backtest Results ===")
        print(f"Starting Portfolio Value: ${start_value:.2f}")
        print(f"Final Portfolio Value: ${end_value:.2f}")
        print(f"Total Return: {total_return:.2f}%")
        
        # Additional metrics could be calculated here
        # For now, we'll just print basic info
        
        return {
            "strategy": strategy_name,
            "start_value": start_value,
            "end_value": end_value,
            "total_return": total_return
        }

def run_comprehensive_backtest():
    """Run a comprehensive backtest with multiple strategies."""
    # Strategies to test
    strategies = [
        (ScalpingStrategy, "ScalpingStrategy"),
        (ScalpingJulyStrategy, "ScalpingJulyStrategy")
    ]
    
    # Results storage
    all_results = []
    
    # Run backtest for each strategy
    for strategy_class, strategy_name in strategies:
        logger.info(f"Running backtest for {strategy_name}")
        
        # Create a cerebro entity
        cerebro = bt.Cerebro()
        
        # Set up initial cash
        cerebro.broker.setcash(1000.0)
        
        # Set commission (0.1% per trade)
        cerebro.broker.setcommission(commission=0.001)
        
        # Set position size
        cerebro.broker.setpositionSizer(bt.sizers.PercentSizer, percents=10)  # 10% of portfolio per trade
        
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
        cerebro.addstrategy(strategy_class)
        
        # Print out the starting conditions
        print(f'\n{strategy_name} - Starting Portfolio Value: ${cerebro.broker.getvalue():.2f}')
        
        # Run over everything
        results = cerebro.run()
        
        # Analyze results
        analyzer = BacktestAnalyzer()
        result = analyzer.analyze_results(cerebro, results, strategy_name)
        all_results.append(result)
        
        # Print out the final result
        print(f'{strategy_name} - Final Portfolio Value: ${cerebro.broker.getvalue():.2f}')
    
    # Print comparison
    print("\n=== Strategy Comparison ===")
    for result in all_results:
        print(f"{result['strategy']}: {result['total_return']:.2f}% return")

def run_single_pair_backtest(pair: str = "BTC_USDT", timeframe: str = "1m"):
    """
    Run backtest for a single pair.
    
    Args:
        pair (str): Trading pair (e.g., "BTC_USDT")
        timeframe (str): Timeframe (e.g., "1m", "5m")
    """
    logger.info(f"Running backtest for {pair} {timeframe}")
    
    # Create a cerebro entity
    cerebro = bt.Cerebro()
    
    # Set up initial cash
    cerebro.broker.setcash(1000.0)
    
    # Set commission (0.1% per trade)
    cerebro.broker.setcommission(commission=0.001)
    
    # Set position size
    cerebro.broker.setpositionSizer(bt.sizers.PercentSizer, percents=10)  # 10% of portfolio per trade
    
    # Load data
    converter = FreqTradeConverter()
    loader = BacktraderDataLoader()
    
    # Try to load data
    data_file = f"user_data/data/binance/{pair}-{timeframe}.json"
    
    if os.path.exists(data_file):
        logger.info(f"Loading data from {data_file}")
        data_feed = loader.load_from_freqtrade_json(data_file, pair)
        cerebro.adddata(data_feed)
    else:
        logger.warning(f"Data file {data_file} not found.")
        return
    
    # Add strategy
    cerebro.addstrategy(ScalpingStrategy)
    
    # Print out the starting conditions
    print(f'\n{pair} {timeframe} - Starting Portfolio Value: ${cerebro.broker.getvalue():.2f}')
    
    # Run over everything
    results = cerebro.run()
    
    # Print out the final result
    print(f'{pair} {timeframe} - Final Portfolio Value: ${cerebro.broker.getvalue():.2f}')
    
    # Plot the result
    cerebro.plot()

if __name__ == "__main__":
    # Run comprehensive backtest
    run_comprehensive_backtest()
    
    # Optionally run single pair backtest
    # run_single_pair_backtest("BTC_USDT", "1m")