#!/bin/bash

echo "Testing CONSERVATIVE Multi-Horizon Momentum Strategy v8.1"
echo "========================================================"

docker compose run --rm freqtrade backtesting \
  -s MultiHorizonMomentum \
  -p BTC/USDT \
  --timerange 20250101-20250712 \
  --fee 0.0002 \
  --timeframe 1m \
  --export trades \
  --export-filename backtest_conservative_$(date +%Y%m%d_%H%M%S)

echo ""
echo "✅ Backtest completed! Check results above."
echo "🎯 Target: Win rate >25% and reduced losses"
echo "📊 v7 baseline: 23.1% win rate, -1.53% total return"
echo "📊 v8 failed: 12.3% win rate, -4.28% total return" 