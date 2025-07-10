#!/bin/bash

echo "🛠️  TESTING v8.4 FIXED: custom_exit Logic Corrected"
echo "==================================================="
echo "BREAKTHROUGH: custom_exit was closing 81/82 trades as losses"
echo ""
echo "KEY FIXES:"
echo "✅ FIXED: custom_exit with conservative distances"
echo "  - Take profit: 5.0x ATR (was 3.5x)"
echo "  - Trail trigger: 2.5x ATR profit required"
echo "  - Trail distance: 1.8x ATR from peak"
echo "✅ FIXED: custom_stoploss 2.5x ATR (was 1.8x)"
echo "✅ PROVEN: Entry logic works perfectly (ultra-selective)"
echo ""
echo "EXPECTED OUTCOME:"
echo "- v8.1-8.3: 0% win rate (broken custom_exit)"
echo "- v8.4: Should return to 30-40% win rate 🎯"
echo ""

# Test with the fixed version
echo "Testing v8.4 FIXED - Expected: Return to normal win rate 🚀"
freqtrade backtesting \
  --strategy MultiHorizonMomentum \
  --config user_data/config.json \
  --pairs BTC/USDT \
  --timeframe 1m \
  --timerange 20241201-20241215 \
  --fee 0.025 \
  --export trades \
  --export-filename user_data/backtest_results/backtest-v8-4-FIXED-working.json

echo ""
echo "✅ v8.4 FIXED test completed!"
echo ""
echo "SUCCESS METRICS:"
echo "- Win rate: Should be 30-40% (vs 0% in v8.1-8.3)"
echo "- Trade count: Should be 30-60 trades (vs 82 broken trades)"
echo "- P&L: Should be significantly better than -80 USDT"
echo "- Exit tags: Should see 'atr_tp_5x' and 'atr_trail_conservative'"
echo ""
echo "If successful: Strategy is WORKING and ready for optimization!"
echo "If failed: May need further custom_exit tuning or deeper investigation" 