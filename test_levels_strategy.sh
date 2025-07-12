#!/bin/bash

echo "Testing ScalpingLevelsStrategy - Based on Professional Trading Video"
echo "================================================================="

docker compose run --rm freqtrade backtesting \
  -s ScalpingLevelsStrategy \
  -p BTC/USDT \
  --timerange 20250101-20250712 \
  --fee 0.0002 \
  --timeframe 1m \
  --export trades \
  --export-filename user_data/backtest_results/levels_strategy_results.json

echo ""
echo "Completed! Compare with original strategy results:"
echo "Original: 681 trades, 23.1% win rate, -1.53% return"
echo "Check the results above for improvement." 