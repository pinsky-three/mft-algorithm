#!/bin/bash

echo "🔧 TESTING v8.1 CONSERVATIVE: Emergency Rollback After v8 Disaster"
echo "================================================================="
echo "v8 RESULTS: 0% win rate, 59 consecutive losses, -46.3 USDT ❌"
echo "v7 BASELINE: 42.1% win rate, -1.54 USDT ⚠️"
echo ""
echo "CONSERVATIVE CHANGES:"
echo "✅ KEEP: Maker fees (0.02% entry/exit)"
echo "🔄 REVERT: SL 1.6x → 1.8x ATR (more noise tolerance)"
echo "❌ REMOVE: EU-US session filter (was killing opportunities)"
echo "🔄 REVERT: Market stoploss (better execution)"
echo ""
echo "TARGET: Recover to v7 performance with modest fee improvement"
echo ""

# Test with blended fees (maker entry/exit, market SL)
echo "Testing CONSERVATIVE v8.1 - Expected: Return to ~40% win rate 🎯"
freqtrade backtesting \
  --strategy MultiHorizonMomentum \
  --config user_data/config.json \
  --pairs BTC/USDT \
  --timeframe 1m \
  --timerange 20241201-20241215 \
  --fee 0.025 \
  --export trades \
  --export-filename user_data/backtest_results/backtest-v8-1-CONSERVATIVE-recovery.json

echo ""
echo "✅ v8.1 CONSERVATIVE test completed!"
echo "Expected vs v7:"
echo "- Win rate: Should recover to ~40-42% (vs 42.1% v7)"
echo "- Trade count: Should return to ~90-95 trades (vs 95 v7)"  
echo "- P&L: Target -1.0 to -1.5 USDT (vs -1.54 v7)"
echo "- Key lesson: Sometimes less optimization = better results"
echo ""
echo "If successful: Modest improvement ready for out-of-sample validation"
echo "If failed: Deeper issues require fundamental strategy revision" 