#!/bin/bash

echo "Testing IMPROVED ScalpingLevelsStrategy - Optimized Risk Management"
echo "=================================================================="
echo "Changes: 1:1.5 R/R, 12h max hold, 1.5x volume, 1.0 ATR stop, 0.5% quick profit"
echo ""

docker compose run --rm freqtrade backtesting \
  -s ScalpingLevelsStrategy \
  -p BTC/USDT \
  --timerange 20250101-20250712 \
  --fee 0.0002 \
  --timeframe 1m \
  --export trades \
  --export-filename user_data/backtest_results/levels_improved_results.json

echo ""
echo "Results comparison:"
echo "Original: 681 trades, 23.1% win rate, -1.53% return"
echo "Levels v1: 3423 trades, 84.6% win rate, -2.27% return"
echo "Levels v2: Check results above for improvement!" 