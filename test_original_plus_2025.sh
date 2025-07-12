#!/bin/bash

echo "Testing ORIGINAL+ Multi-Horizon Momentum Strategy v7.1"
echo "======================================================"

docker compose run --rm freqtrade backtesting \
  -s MultiHorizonMomentum \
  -p BTC/USDT \
  --timerange 20250101-20250712 \
  --fee 0.0002 \
  --timeframe 1m \
  --export trades \
  --export-filename backtest_original_plus_$(date +%Y%m%d_%H%M%S)

echo ""
echo "✅ Backtest completed! Check results above."
echo "🎯 Target: Match v7 baseline performance"
echo "📊 v7 baseline: 681 trades, 23.1% win rate, -1.53% total return"
echo "📊 Expected: ~681 trades, ~23% win rate, hopefully improved returns" 