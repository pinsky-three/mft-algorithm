#!/bin/bash

echo "🏆 Testing CryptoScalpingOptimized - FINAL VERSION"
echo "=================================================="
echo ""
echo "🎯 GOAL: First PROFITABLE crypto scalping strategy!"
echo ""
echo "📊 Based on proven hybrid (126 trades, 56.3% win rate, -0.18% loss)"
echo "🔧 Optimizations:"
echo "   ✅ Looser filters (more trades: 300-500 target)"
echo "   ✅ Enhanced momentum detection (70% threshold)"  
echo "   ✅ Better profit targets (2.5x ratio)"
echo "   ✅ Improved level detection (1.2% proximity)"
echo "   ✅ Faster EMAs (10/21/42 periods)"
echo ""

docker compose run --rm freqtrade backtesting \
  -s CryptoScalpingOptimized \
  -p BTC/USDT \
  --timerange 20250101-20250712 \
  --fee 0.0002 \
  --timeframe 5m \
  --export trades \
  --export-filename user_data/backtest_results/final_optimized_results.json

echo ""
echo "🎯 === FINAL PERFORMANCE COMPARISON ==="
echo "Original:          681 trades, 23.1% win rate, -1.53% return"
echo "Levels v1:        3423 trades, 84.6% win rate, -2.27% return"  
echo "Levels v2:        6026 trades, 76.9% win rate, -4.56% return"
echo "Hybrid:            126 trades, 56.3% win rate, -0.18% return ⭐"
echo "OPTIMIZED FINAL:   Check results above! 🚀"
echo ""
echo "🎯 TARGET: 300-500 trades, 55-65% win rate, POSITIVE return!"
echo "🏆 SUCCESS = Beat BTC's +21.37% performance during same period" 