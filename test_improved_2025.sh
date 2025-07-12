#!/bin/bash

echo "Testing IMPROVED Multi-Horizon Momentum Strategy v8"
echo "==================================================="

docker compose run --rm freqtrade backtesting \
  -s MultiHorizonMomentum \
  -p BTC/USDT \
  --timerange 20250101-20250712 \
  --fee 0.0002 \
  --timeframe 1m \
  --export trades \
  --export-filename backtest_improved_$(date +%Y%m%d_%H%M%S)

echo ""
echo "✅ Backtest completed! Check results above."
echo "🎯 Target: Win rate >30% and positive returns"
echo "📊 Previous: 23.1% win rate, -1.53% total return" 