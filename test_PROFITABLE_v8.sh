#!/bin/bash

echo "🚀 TESTING v8 PROFITABLE: Maker Fees + Optimized R:R + EU-US Sessions"
echo "===================================================================="
echo "BREAKTHROUGH TARGET: From -1.54 USDT (v7) to +2-4 USDT PROFIT!"
echo ""
echo "Key optimizations:"
echo "- 100% Maker fees (0.02% vs 0.04% = +2-3 USDT impact)"
echo "- SL 1.6x ATR, TP 3.5x ATR (better R:R)"
echo "- EU-US trading sessions only (high volatility)"
echo "- v7 baseline: 42.1% win rate, -1.54 USDT"
echo ""

# Test with realistic maker fees (0.02%)
echo "Testing with MAKER FEES (0.02%) - Expected: PROFITABLE 🎯"
freqtrade backtesting \
  --strategy MultiHorizonMomentum \
  --config user_data/config.json \
  --pairs BTC/USDT \
  --timeframe 1m \
  --timerange 20241201-20241215 \
  --fee 0.02 \
  --export trades \
  --export-filename user_data/backtest_results/backtest-v8-PROFITABLE-maker-fees.json

echo ""
echo "✅ v8 PROFITABLE test completed!"
echo "Expected improvements:"
echo "- Maker fees: +2-3 USDT vs v7"
echo "- Better R:R: +1-2 USDT vs v7"  
echo "- Session filter: +0.5-1 USDT vs v7"
echo "- TOTAL EXPECTED: +3.5-6 USDT → PROFITABLE!"
echo ""
echo "Check results: 95 trades → ~60-70 trades (session filter)"
echo "Win rate: 42.1% → 45-50% (better R:R + sessions)"
echo "P&L: -1.54 USDT → +2-4 USDT PROFIT TARGET! 🚀" 