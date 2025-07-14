#!/bin/bash

echo "🚀 PHASE 3 BALANCED TEST - January 2025"
echo "========================================"
echo "Testing Phase 3 Balanced strategy with calibrated thresholds"
echo ""

# Test just January 2025 with Phase 3 Balanced strategy
timerange="20250101-20250201"
strategy="CryptoScalpingPhase3Balanced"

echo "🔄 Testing Phase 3 Balanced strategy for January 2025..."
echo "Strategy: $strategy (calibrated thresholds)"
echo "Timerange: $timerange"
echo "Pairs: BTC/USDT ETH/USDT SOL/USDT"
echo ""

# Key differences from strict Phase 3:
echo "📊 BALANCED CALIBRATIONS vs STRICT PHASE 3:"
echo "   • Market Health: 0.65 (vs 0.7 strict)"
echo "   • Volume Quality: 0.75 (vs 0.85 strict)" 
echo "   • Entry Selectivity: 0.75 (vs 0.85 strict)"
echo "   • Smart Money Threshold: 0.65 (vs 0.75 strict)"
echo "   • Market Regime Strictness: 0.7 (vs 0.8 strict)"
echo ""

# Run the backtest
echo "🚀 Starting backtest..."
docker compose run --rm freqtrade backtesting \
    -s "$strategy" \
    -p BTC/USDT ETH/USDT SOL/USDT \
    --timerange "$timerange" \
    --fee 0.0002 \
    --timeframe 1m

echo ""
echo "✅ Balanced test completed!" 