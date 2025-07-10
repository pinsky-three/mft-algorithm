#!/bin/bash

echo "🧪 TESTING v8.2 DIAGNOSIS: custom_stoploss DISABLED"
echo "==================================================="
echo "HYPOTHESIS: custom_stoploss is causing 0% win rate by immediate exits"
echo ""
echo "TEST CHANGES:"
echo "❌ DISABLED: custom_stoploss (return 1 - no custom SL)"
echo "⚠️  FALLBACK: Strategy stoploss (-30%) only"
echo "✅ KEEP: All entry filters (EMA + RSI>60 + MACD + Volume)"
echo "✅ KEEP: custom_exit (ATR TP + trailing)"
echo ""
echo "EXPECTED OUTCOME:"
echo "- If custom_stoploss WAS the bug: Win rate should return to ~40%"
echo "- If NOT the bug: Still 0% win rate (deeper problem)"
echo ""

# Test diagnosis version
echo "Testing v8.2 DIAGNOSIS - Expected: Significant improvement if SL was the bug 🔬"
freqtrade backtesting \
  --strategy MultiHorizonMomentum \
  --config user_data/config.json \
  --pairs BTC/USDT \
  --timeframe 1m \
  --timerange 20241201-20241215 \
  --fee 0.025 \
  --export trades \
  --export-filename user_data/backtest_results/backtest-v8-2-DIAGNOSIS-no-custom-sl.json

echo ""
echo "✅ v8.2 DIAGNOSIS test completed!"
echo ""
echo "INTERPRETATION:"
echo "- If win rate ~40%: custom_stoploss WAS the bug ✅"
echo "- If win rate still 0%: Bug is elsewhere (entry logic, data, etc.) ❌"
echo "- If mixed results: Partial improvement, need deeper analysis 🤔"
echo ""
echo "Next steps based on results:"
echo "SUCCESS → Fix custom_stoploss logic and retest"
echo "FAILED → Investigate entry conditions, ATR calculation, or data quality" 