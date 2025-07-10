#!/bin/bash

echo "🎯 TESTING v8.5 ULTRA SIMPLE: Only Take Profit, NO Trailing"
echo "============================================================"
echo "v8.4 FAILED: Still 0% win rate even with conservative trailing"
echo ""
echo "v8.5 RADICAL SIMPLIFICATION:"
echo "✅ ONLY: 4x ATR take profit"
echo "❌ DISABLED: All trailing stop logic (was causing 0% win rate)"
echo "✅ KEEP: 2.5x ATR custom_stoploss"
echo "✅ BACKUP: -30% strategy stoploss"
echo ""
echo "HYPOTHESIS:"
echo "- Trailing logic was prematurely closing ALL trades as losses"
echo "- Simple TP should allow some trades to win naturally"
echo ""
echo "EXPECTED OUTCOME:"
echo "- v8.1-8.4: 0% win rate (broken trailing logic)"
echo "- v8.5: Should see SOME winners at 4x ATR take profit 🎯"
echo ""

# Test with the ultra simple version
echo "Testing v8.5 ULTRA SIMPLE - Expected: Some wins at 4x ATR TP 🚀"
freqtrade backtesting \
  --strategy MultiHorizonMomentum \
  --config user_data/config.json \
  --pairs BTC/USDT \
  --timeframe 1m \
  --timerange 20241201-20241215 \
  --fee 0.025 \
  --export trades \
  --export-filename user_data/backtest_results/backtest-v8-5-ULTRA-SIMPLE-working.json

echo ""
echo "✅ v8.5 ULTRA SIMPLE test completed!"
echo ""
echo "SUCCESS METRICS:"
echo "- Win rate: Should be >0% (even 5-10% would be progress)"
echo "- Exit tags: Should see 'atr_tp_4x_simple' for winners"
echo "- Trade duration: Should be longer (not prematurely closed)"
echo "- P&L: Should be better than -69 USDT (any improvement counts)"
echo ""
echo "If successful: Trailing logic WAS the problem - can optimize TP level"
echo "If failed: Need deeper investigation into custom_stoploss or ATR values" 