# Backtrader Integration

This directory contains the Backtrader integration for the MFT algorithm project. It provides backtesting and analysis capabilities that complement the existing FreqTrade setup for live trading.

## Overview

The Backtrader integration allows you to:

1. Backtest trading strategies using historical data
2. Analyze strategy performance with detailed metrics
3. Optimize strategy parameters
4. Compare different strategies
5. Visualize trading results

## Directory Structure

```
backtrader/
├── strategies/        # Backtrader trading strategies
├── data/             # Data handling utilities
├── analysis/         # Analysis tools and metrics
├── utils/            # Utility functions
├── examples/         # Example scripts
├── tests/            # Test files
├── config/           # Configuration files
└── notebooks/        # Jupyter notebooks
```

## Getting Started

### Prerequisites

- Python 3.8+
- Docker (optional, for containerized execution)
- The dependencies listed in `backtrader_requirements.txt`

### Installation

1. Install the required dependencies:
   ```bash
   pip install -r backtrader_requirements.txt
   ```

2. Or use Docker:
   ```bash
   docker-compose -f docker-compose.backtrader.yml up
   ```

### Running Backtests

1. Simple backtest:
   ```bash
   python backtrader/examples/simple_backtest.py
   ```

2. Comprehensive backtest:
   ```bash
   python backtrader/examples/comprehensive_backtest.py
   ```

3. Parameter optimization:
   ```bash
   python backtrader/examples/optimization_example.py
   ```

## Data Integration

The integration includes utilities to convert FreqTrade JSON data to Backtrader-compatible format:

- `freqtrade_converter.py`: Converts FreqTrade JSON data
- `data_loader.py`: Loads data into Backtrader

## Strategies

Currently implemented strategies:

1. `ScalpingStrategy`: Mirrors the CryptoScalpingOptimized strategy
2. `ScalpingJulyStrategy`: Mirrors the CryptoScalpingOptimizedJuly strategy

## Development

### Adding New Strategies

1. Create a new strategy file in `backtrader/strategies/`
2. Extend the `BaseStrategy` class
3. Implement the `next()` method with your trading logic
4. Add the strategy to the examples or create a new example script

### Adding New Indicators

1. Add indicator computation methods to `BaseStrategy`
2. Use the existing pattern for consistency

## Testing

Run tests with:
```bash
python -m pytest backtrader/tests/
```

## Docker Usage

### Building the Image

```bash
docker build -f Dockerfile.backtrader -t backtrader-mft .
```

### Running with Docker

```bash
docker run --rm -v ./user_data:/app/user_data backtrader-mft
```

### Using Docker Compose

```bash
docker-compose -f docker-compose.backtrader.yml up
```

## Comparison with FreqTrade

The Backtrader integration is designed to complement, not replace, the existing FreqTrade setup:

- **FreqTrade**: Live trading, real-time execution
- **Backtrader**: Backtesting, analysis, strategy development

Both systems can coexist and share the same data directory structure.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## License

This project follows the same license as the main MFT algorithm project.