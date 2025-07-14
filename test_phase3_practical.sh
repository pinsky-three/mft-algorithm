#!/bin/bash

echo "🚀 PHASE 3 PRACTICAL TEST - January 2025"
echo "========================================"
echo "Testing Phase 3 Practical strategy with simplified but effective logic"
echo ""

echo "🔄 Testing Phase 3 Practical strategy for January 2025..."
echo "Strategy: CryptoScalpingPhase3Practical (simplified approach)"
echo "Timerange: 20250101-20250201"
echo "Pairs: BTC/USDT ETH/USDT SOL/USDT"
echo ""

echo "📊 PRACTICAL IMPROVEMENTS vs PHASE 3:"
echo "   • Entry Logic: 3 key filters (vs 9+ complex ones)"
echo "   • Volume Analysis: Simple ratios (vs complex smart money detection)"
echo "   • Market Health: 5-factor score (vs multi-layer complexity)"
echo "   • No ML regime detection (caused over-filtering)"
echo "   • Keep: Adaptive targets, performance feedback, trade limits"
echo ""

echo "🚀 Starting backtest..."

# Run the backtest
docker compose run --rm freqtrade backtesting \
  -s CryptoScalpingPhase3Practical \
  -p BTC/USDT ETH/USDT SOL/USDT \
  --timerange 20250101-20250201 \
  --fee 0.0002 \
  --timeframe 1m

echo ""
echo "✅ Phase 3 Practical test completed!" 