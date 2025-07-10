#!/bin/bash

echo "🧪 TESTING v8.6 COMPLETE DISABLE: NO custom_exit Logic"
echo "======================================================"
echo "v8.5 SIGNIFICANT PROGRESS: -16.7 vs -69.656 USDT (76% better!)"
echo "But still 17/18 trades closed by custom_exit with 0% win rate"
echo ""
echo "v8.6 COMPLETE DISABLE HYPOTHESIS:"
echo "❌ DISABLE: ALL custom_exit logic completely"
echo "✅ ONLY: custom_stoploss (2.5x ATR) + strategy SL (-30%)"
echo "✅ TEST: Let trades run to natural conclusions"
echo "✅ VALIDATE: Are trades hitting ANY profitable exits?"
echo ""
echo "COMPARISON EXPECTATIONS:"
echo "- v8.5: 18 trades, -16.7 USDT, 14:58 avg duration"
echo "- v8.6: Should see longer trades, maybe some force_exit winners"
echo "- KEY: Exit reasons should show ZERO custom_exit"
echo ""

# Test with completely disabled custom_exit
echo "Testing v8.6 COMPLETE DISABLE - Let market decide! 🚀"
freqtrade backtesting \
  --strategy MultiHorizonMomentum \
  --config user_data/config.json \
  --pairs BTC/USDT \
  --timeframe 1m \
  --timerange 20241201-20241215 \
  --fee 0.025 \
  --export trades \
  --export-filename user_data/backtest_results/backtest-v8-6-COMPLETE-DISABLE.json

echo ""
echo "✅ v8.6 COMPLETE DISABLE test completed!"
echo ""
echo "CRITICAL ANALYSIS:"
echo "- Exit reasons: Should show ONLY custom_stoploss and force_exit"
echo "- Duration: Should be even longer than v8.5's 14:58:00"
echo "- Trade count: Might be lower with longer hold times"
echo "- Win rate: Hoping for >0% if any trades run to natural profit"
echo ""
echo "BREAKTHROUGH MOMENT:"
echo "If v8.6 shows ANY winners: custom_exit was 100% the problem"
echo "If v8.6 still 0% winners: custom_stoploss needs investigation" 