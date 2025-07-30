# Getting Started with Backtrader Integration

This guide will help you get started with using the Backtrader integration for backtesting and analysis.

## Prerequisites

Before you begin, ensure you have:

1. Python 3.8 or higher installed
2. Access to the MFT algorithm repository
3. FreqTrade data in JSON format (in `user_data/data/`)

## Installation

### Option 1: Direct Installation

1. Install the required dependencies:
   ```bash
   pip install -r backtrader_requirements.txt
   ```

2. Verify the installation:
   ```bash
   python -c "import backtrader; print('Backtrader installed successfully')"
   ```

### Option 2: Using Docker

1. Build the Docker image:
   ```bash
   docker build -f Dockerfile.backtrader -t backtrader-mft .
   ```

2. Run the container:
   ```bash
   docker run --rm -v ./user_data:/app/user_data backtrader-mft
   ```

## Running Your First Backtest

### Using the Command Line

1. Run a simple backtest:
   ```bash
   python backtrader/examples/simple_backtest.py
   ```

2. Run a comprehensive backtest:
   ```bash
   python backtrader/examples/comprehensive_backtest.py
   ```

### Using Docker

```bash
docker-compose -f docker-compose.backtrader.yml up
```

## Understanding the Data Flow

1. **Data Source**: FreqTrade JSON data in `user_data/data/binance/`
2. **Conversion**: `freqtrade_converter.py` converts JSON to pandas DataFrame
3. **Loading**: `data_loader.py` loads DataFrame into Backtrader format
4. **Backtesting**: Strategies process the data and generate trades
5. **Analysis**: Results are analyzed and visualized

## Customizing Strategies

### Modifying Parameters

Strategies have configurable parameters that can be adjusted:

```python
# Example: Modify RSI threshold
cerebro.addstrategy(ScalpingStrategy, rsi_threshold=60)
```

### Creating New Strategies

1. Create a new file in `backtrader/strategies/`
2. Extend `BaseStrategy`:
   ```python
   from backtrader.strategies.base_strategy import BaseStrategy
   
   class MyStrategy(BaseStrategy):
       params = (
           ('my_param', 10),
       )
       
       def __init__(self):
           super().__init__()
           # Initialize indicators
           
       def next(self):
           # Implement trading logic
           pass
   ```

## Analyzing Results

### Performance Metrics

The backtesting scripts automatically calculate:

- Total return
- Sharpe ratio
- Maximum drawdown
- Win rate
- Profit factor

### Visualization

Backtrader provides built-in plotting capabilities:

```python
cerebro.plot()
```

## Parameter Optimization

Run parameter optimization to find the best strategy settings:

```bash
python backtrader/examples/optimization_example.py
```

## Best Practices

### Data Quality

1. Ensure data is clean and complete
2. Check for missing values or anomalies
3. Verify data timestamps are consistent

### Strategy Development

1. Start with simple strategies
2. Gradually add complexity
3. Test with out-of-sample data
4. Validate results against FreqTrade backtesting

### Performance Considerations

1. Use appropriate timeframes for your strategy
2. Limit the number of indicators to improve performance
3. Consider memory usage with large datasets

## Troubleshooting

### Common Issues

1. **Data not found**: Verify the path to `user_data/data/`
2. **Import errors**: Check that all dependencies are installed
3. **Memory errors**: Reduce the dataset size or use data filtering

### Getting Help

1. Check the logs for error messages
2. Verify your data format matches expectations
3. Consult the Backtrader documentation

## Next Steps

1. Experiment with different strategies
2. Optimize strategy parameters
3. Compare strategy performance
4. Integrate with Jupyter notebooks for interactive analysis