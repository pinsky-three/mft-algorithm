#!/bin/bash

echo "🎯 FINAL OPTIMIZATION VALIDATION - COMPREHENSIVE BACKTEST"
echo "=========================================================="
echo "Testing optimized ROI parameters (3.0%/2.5%/2.0%) vs baseline"
echo "Period: January 2025 - July 2025 (6+ months)"
echo "Pairs: BTC/USDT, ETH/USDT, SOL/USDT"
echo ""

# Full period backtest
echo "🔄 Running comprehensive backtest with optimized parameters..."
docker compose run --rm freqtrade backtesting \
    -s CryptoScalpingOptimized \
    -p BTC/USDT ETH/USDT SOL/USDT \
    --timerange 20250101-20250710 \
    --fee 0.0002 \
    --timeframe 1m \
    --export trades \
    --export-filename optimized_results.json

echo ""
echo "✅ Comprehensive backtest complete!"
echo "📊 Results include full period performance with optimized ROI parameters"
echo "💡 Compare against baseline: 8.745 USDT profit, 254 trades" 