#!/bin/bash

echo "🚀 PHASE 3 QUICK TEST - January 2025"
echo "====================================="
echo "Testing Phase 3 strategy for one month to validate implementation"
echo ""

# Test just January 2025 with Phase 3 strategy
timerange="20250101-20250201"
strategy="CryptoScalpingPhase3"

echo "🔄 Testing Phase 3 strategy for January 2025..."
echo "Strategy: $strategy"
echo "Timerange: $timerange"
echo "Pairs: BTC/USDT ETH/USDT SOL/USDT"
echo ""

# Run the backtest with verbose output to see what's happening
echo "🚀 Starting backtest..."
docker compose run --rm freqtrade backtesting \
    -s "$strategy" \
    -p BTC/USDT ETH/USDT SOL/USDT \
    --timerange "$timerange" \
    --fee 0.0002 \
    --timeframe 1m

echo ""
echo "✅ Test completed!" 