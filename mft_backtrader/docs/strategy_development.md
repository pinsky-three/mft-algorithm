# Strategy Development Guide

This guide explains how to develop and customize trading strategies using the Backtrader integration.

## Understanding the Base Strategy

All strategies should extend the `BaseStrategy` class, which provides common functionality:

```python
from backtrader.strategies.base_strategy import BaseStrategy

class MyStrategy(BaseStrategy):
    params = (
        ('my_param', 10),
    )
    
    def __init__(self):
        super().__init__()
        # Initialize indicators and variables
        
    def next(self):
        # Implement trading logic
        pass
```

## Key Components

### Parameters

Define strategy parameters using the `params` tuple:

```python
params = (
    ('ema_fast_period', 10),
    ('ema_slow_period', 21),
    ('rsi_period', 14),
    ('rsi_threshold', 70),
)
```

Access parameters in your code with `self.p.parameter_name`.

### Initialization

In the `__init__` method:

1. Call `super().__init__()`
2. Initialize indicators using helper methods
3. Set up any required variables

```python
def __init__(self):
    super().__init__()
    
    # Initialize indicators
    self.ema_fast = self.compute_ema(self.data.close, self.p.ema_fast_period)
    self.ema_slow = self.compute_ema(self.data.close, self.p.ema_slow_period)
    self.rsi = self.compute_rsi(self.data.close, self.p.rsi_period)
```

### Trading Logic

Implement your trading logic in the `next` method, which is called for each bar:

```python
def next(self):
    # Entry condition
    if not self.position and self.should_enter():
        self.buy()
    
    # Exit condition
    elif self.position and self.should_exit():
        self.sell()
```

## Available Indicators

The `BaseStrategy` class provides helper methods for common indicators:

### Moving Averages

```python
# EMA
ema = self.compute_ema(data, period)

# SMA
sma = bt.indicators.SMA(data, period=period)
```

### Oscillators

```python
# RSI
rsi = self.compute_rsi(data, period)

# MACD
macd_dict = self.compute_macd(data, fast, slow, signal)
```

### Volatility Indicators

```python
# ATR
atr = self.compute_atr(data, period)
```

### Volume Indicators

```python
# Volume SMA
volume_sma = self.compute_volume_sma(data, period)

# Volume Ratio
volume_ratio = self.compute_volume_ratio(data, period)
```

## Strategy Patterns

### Simple Moving Average Crossover

```python
def __init__(self):
    super().__init__()
    self.sma_fast = self.compute_ema(self.data.close, 10)
    self.sma_slow = self.compute_ema(self.data.close, 20)

def next(self):
    if not self.position:
        if self.sma_fast[0] > self.sma_slow[0]:
            self.buy()
    else:
        if self.sma_fast[0] < self.sma_slow[0]:
            self.sell()
```

### RSI Mean Reversion

```python
def __init__(self):
    super().__init__()
    self.rsi = self.compute_rsi(self.data.close, 14)

def next(self):
    if not self.position:
        if self.rsi[0] < 30:  # Oversold
            self.buy()
    else:
        if self.rsi[0] > 70:  # Overbought
            self.sell()
```

## Risk Management

### Position Sizing

Set position sizing when adding the strategy to Cerebro:

```python
cerebro.broker.setpositionSizer(bt.sizers.PercentSizer, percents=10)
```

### Stop Loss

Implement stop loss in your strategy:

```python
def next(self):
    if self.position:
        # 5% stop loss
        if self.data.close[0] < self.position.price * 0.95:
            self.sell()
```

### Take Profit

Implement take profit:

```python
def next(self):
    if self.position:
        # 10% take profit
        if self.data.close[0] > self.position.price * 1.10:
            self.sell()
```

## Advanced Features

### Multiple Timeframes

Add multiple data feeds for different timeframes:

```python
# In your backtest script
data_1m = loader.load_from_freqtrade_json("BTC_USDT-1m.json")
data_15m = loader.load_from_freqtrade_json("BTC_USDT-15m.json")

cerebro.adddata(data_1m)
cerebro.adddata(data_15m)
```

Access in strategy:
```python
def __init__(self):
    self.data_1m = self.datas[0]  # 1-minute data
    self.data_15m = self.datas[1]  # 15-minute data
```

### Custom Indicators

Create custom indicators by extending `bt.Indicator`:

```python
class MyIndicator(bt.Indicator):
    lines = ('my_line',)
    params = (('period', 14),)
    
    def __init__(self):
        # Calculate indicator values
        pass
    
    def next(self):
        # Update indicator for current bar
        self.lines.my_line[0] = calculated_value
```

## Converting from FreqTrade

When converting FreqTrade strategies:

1. Map parameters exactly
2. Recreate indicator calculations
3. Implement identical entry/exit conditions
4. Validate with the same data

### Example Conversion

FreqTrade:
```python
dataframe['ema_fast'] = ta.EMA(dataframe, timeperiod=10)
dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
```

Backtrader:
```python
self.ema_fast = self.compute_ema(self.data.close, 10)
self.rsi = self.compute_rsi(self.data.close, 14)
```

## Testing Strategies

### Unit Testing

Create tests for individual components:

```python
def test_ema_calculation():
    # Test EMA computation
    pass
```

### Integration Testing

Test complete strategy logic with sample data.

### Validation

Compare results with FreqTrade backtesting to ensure consistency.

## Performance Optimization

### Indicator Efficiency

1. Precompute static indicators in `__init__`
2. Avoid redundant calculations
3. Use built-in indicators when possible

### Memory Management

1. Limit data loading to required time periods
2. Use data compression for large datasets
3. Clean up unused variables

## Best Practices

### Code Organization

1. Keep strategies focused on single trading ideas
2. Use helper methods for complex logic
3. Document parameter purposes
4. Follow consistent naming conventions

### Strategy Design

1. Start simple and add complexity gradually
2. Validate with out-of-sample data
3. Consider transaction costs and slippage
4. Test with different market conditions

### Error Handling

1. Handle missing data gracefully
2. Validate input parameters
3. Log important events and errors
4. Implement fallback logic for edge cases

## Debugging Strategies

### Logging

Use the built-in logging functionality:

```python
self.log("Debug message", debug=True)
```

### Visualization

Plot indicators and trades to verify logic:

```python
cerebro.plot()
```

### Step-by-Step Execution

Use Backtrader's analyzer features to examine strategy behavior.