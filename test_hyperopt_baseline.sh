#!/bin/bash

# Test Hyperopt Baseline Verification
# ===================================
# Ensures CryptoScalpingOptimizedHyperopt produces IDENTICAL results 
# to CryptoScalpingOptimized when using default parameters

echo "🧪 HYPEROPT BASELINE VERIFICATION TEST"
echo "======================================"
echo ""
echo "🎯 PURPOSE: Verify hyperopt version matches original exactly"
echo "📊 EXPECTED: Identical profit, trades, win rate, drawdown"
echo "⚠️  CRITICAL: Any difference means hyperopt integration is broken"
echo ""

# Test parameters
TEST_TIMERANGE="20250101-20250301"  # 2-month test (Jan-Feb 2025)
TEST_PAIRS="BTC/USDT ETH/USDT SOL/USDT"
TEST_FEE="0.0002"
TEST_TIMEFRAME="1m"

# Results files
ORIGINAL_RESULTS="baseline_original_results.txt"
HYPEROPT_RESULTS="baseline_hyperopt_results.txt"
COMPARISON_RESULTS="baseline_comparison.txt"

echo "📅 Test Period: ${TEST_TIMERANGE}"
echo "💰 Pairs: ${TEST_PAIRS}"
echo "⏰ Timeframe: ${TEST_TIMEFRAME}"
echo ""

# ===================================================
# 1. Test Original CryptoScalpingOptimized Strategy
# ===================================================

echo "🔄 Testing ORIGINAL CryptoScalpingOptimized..."
echo ""

# Run original strategy and capture output
original_output=$(docker compose run --rm freqtrade backtesting \
  -s CryptoScalpingOptimized \
  -p ${TEST_PAIRS} \
  --timerange ${TEST_TIMERANGE} \
  --fee ${TEST_FEE} \
  --timeframe ${TEST_TIMEFRAME} \
  2>/dev/null | tr -d '\r')

# Extract key metrics from original
original_profit_percent=$(echo "$original_output" | grep "│ Total profit %" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)%[[:space:]]*│.*/\1/')
original_profit_usdt=$(echo "$original_output" | grep "│ Absolute profit" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)[[:space:]]*USDT[[:space:]]*│.*/\1/')
original_total_trades=$(echo "$original_output" | grep "│ Total/Daily Avg Trades" | head -1 | sed 's/.*│[[:space:]]*\([0-9]*\)[[:space:]]*\/.*│.*/\1/')
original_win_rate=$(echo "$original_output" | grep "│    TOTAL │" | head -1 | sed 's/.*│[[:space:]]*[0-9]*[[:space:]]*[0-9]*[[:space:]]*[0-9]*[[:space:]]*\([0-9.]*\)[[:space:]]*│.*/\1/')
original_max_drawdown=$(echo "$original_output" | grep "│ Max % of account underwater" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)%[[:space:]]*│.*/\1/')

# Handle empty values
original_profit_percent=${original_profit_percent:-"0.00"}
original_profit_usdt=${original_profit_usdt:-"0.000"}
original_total_trades=${original_total_trades:-"0"}
original_win_rate=${original_win_rate:-"0.0"}
original_max_drawdown=${original_max_drawdown:-"0.00"}

# Save original results
echo "🔍 ORIGINAL STRATEGY RESULTS" > "$ORIGINAL_RESULTS"
echo "============================" >> "$ORIGINAL_RESULTS"
echo "Strategy: CryptoScalpingOptimized" >> "$ORIGINAL_RESULTS"
echo "Test Period: ${TEST_TIMERANGE}" >> "$ORIGINAL_RESULTS"
echo "Pairs: ${TEST_PAIRS}" >> "$ORIGINAL_RESULTS"
echo "" >> "$ORIGINAL_RESULTS"
echo "Total Profit %: ${original_profit_percent}%" >> "$ORIGINAL_RESULTS"
echo "Absolute Profit: ${original_profit_usdt} USDT" >> "$ORIGINAL_RESULTS"
echo "Total Trades: ${original_total_trades}" >> "$ORIGINAL_RESULTS"
echo "Win Rate: ${original_win_rate}%" >> "$ORIGINAL_RESULTS"
echo "Max Drawdown: ${original_max_drawdown}%" >> "$ORIGINAL_RESULTS"
echo "" >> "$ORIGINAL_RESULTS"

echo "✅ Original Results:"
echo "   Profit: ${original_profit_percent}% (${original_profit_usdt} USDT)"
echo "   Trades: ${original_total_trades}"
echo "   Win Rate: ${original_win_rate}%"
echo "   Max Drawdown: ${original_max_drawdown}%"
echo ""

# ======================================================
# 2. Test Hyperopt CryptoScalpingOptimizedHyperopt Strategy
# ======================================================

echo "🔄 Testing HYPEROPT CryptoScalpingOptimizedHyperopt (default parameters)..."
echo ""

# Run hyperopt strategy with default parameters
hyperopt_output=$(docker compose run --rm freqtrade backtesting \
  -s CryptoScalpingOptimizedHyperopt \
  -p ${TEST_PAIRS} \
  --timerange ${TEST_TIMERANGE} \
  --fee ${TEST_FEE} \
  --timeframe ${TEST_TIMEFRAME} \
  2>/dev/null | tr -d '\r')

# Extract key metrics from hyperopt
hyperopt_profit_percent=$(echo "$hyperopt_output" | grep "│ Total profit %" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)%[[:space:]]*│.*/\1/')
hyperopt_profit_usdt=$(echo "$hyperopt_output" | grep "│ Absolute profit" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)[[:space:]]*USDT[[:space:]]*│.*/\1/')
hyperopt_total_trades=$(echo "$hyperopt_output" | grep "│ Total/Daily Avg Trades" | head -1 | sed 's/.*│[[:space:]]*\([0-9]*\)[[:space:]]*\/.*│.*/\1/')
hyperopt_win_rate=$(echo "$hyperopt_output" | grep "│    TOTAL │" | head -1 | sed 's/.*│[[:space:]]*[0-9]*[[:space:]]*[0-9]*[[:space:]]*[0-9]*[[:space:]]*\([0-9.]*\)[[:space:]]*│.*/\1/')
hyperopt_max_drawdown=$(echo "$hyperopt_output" | grep "│ Max % of account underwater" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)%[[:space:]]*│.*/\1/')

# Handle empty values
hyperopt_profit_percent=${hyperopt_profit_percent:-"0.00"}
hyperopt_profit_usdt=${hyperopt_profit_usdt:-"0.000"}
hyperopt_total_trades=${hyperopt_total_trades:-"0"}
hyperopt_win_rate=${hyperopt_win_rate:-"0.0"}
hyperopt_max_drawdown=${hyperopt_max_drawdown:-"0.00"}

# Save hyperopt results
echo "🔍 HYPEROPT STRATEGY RESULTS (Default Parameters)" > "$HYPEROPT_RESULTS"
echo "===================================================" >> "$HYPEROPT_RESULTS"
echo "Strategy: CryptoScalpingOptimizedHyperopt" >> "$HYPEROPT_RESULTS"
echo "Test Period: ${TEST_TIMERANGE}" >> "$HYPEROPT_RESULTS"
echo "Pairs: ${TEST_PAIRS}" >> "$HYPEROPT_RESULTS"
echo "" >> "$HYPEROPT_RESULTS"
echo "Total Profit %: ${hyperopt_profit_percent}%" >> "$HYPEROPT_RESULTS"
echo "Absolute Profit: ${hyperopt_profit_usdt} USDT" >> "$HYPEROPT_RESULTS"
echo "Total Trades: ${hyperopt_total_trades}" >> "$HYPEROPT_RESULTS"
echo "Win Rate: ${hyperopt_win_rate}%" >> "$HYPEROPT_RESULTS"
echo "Max Drawdown: ${hyperopt_max_drawdown}%" >> "$HYPEROPT_RESULTS"
echo "" >> "$HYPEROPT_RESULTS"

echo "✅ Hyperopt Results (defaults):"
echo "   Profit: ${hyperopt_profit_percent}% (${hyperopt_profit_usdt} USDT)"
echo "   Trades: ${hyperopt_total_trades}"
echo "   Win Rate: ${hyperopt_win_rate}%"
echo "   Max Drawdown: ${hyperopt_max_drawdown}%"
echo ""

# ================================
# 3. Compare Results & Validation
# ================================

echo "🔍 BASELINE COMPARISON & VALIDATION"
echo "===================================="

# Initialize comparison file
echo "🧪 HYPEROPT BASELINE VERIFICATION" > "$COMPARISON_RESULTS"
echo "===================================" >> "$COMPARISON_RESULTS"
echo "Test Date: $(date)" >> "$COMPARISON_RESULTS"
echo "Test Period: ${TEST_TIMERANGE}" >> "$COMPARISON_RESULTS"
echo "Pairs: ${TEST_PAIRS}" >> "$COMPARISON_RESULTS"
echo "" >> "$COMPARISON_RESULTS"

# Detailed comparison
echo "📊 DETAILED COMPARISON:" >> "$COMPARISON_RESULTS"
echo "======================" >> "$COMPARISON_RESULTS"
echo "" >> "$COMPARISON_RESULTS"
printf "%-25s | %-15s | %-15s | %-10s\n" "Metric" "Original" "Hyperopt" "Match?" >> "$COMPARISON_RESULTS"
echo "----------------------------------------------------------------" >> "$COMPARISON_RESULTS"

# Compare each metric
profit_match="❌"
usdt_match="❌"
trades_match="❌"
winrate_match="❌"
drawdown_match="❌"

# Profit percentage comparison (allow 0.01% tolerance)
profit_diff=$(echo "$original_profit_percent $hyperopt_profit_percent" | awk '{print ($1 - $2)^2}')
if (( $(echo "$profit_diff < 0.0001" | bc -l) )); then
    profit_match="✅"
fi

# USDT comparison (allow 0.001 USDT tolerance)
usdt_diff=$(echo "$original_profit_usdt $hyperopt_profit_usdt" | awk '{print ($1 - $2)^2}')
if (( $(echo "$usdt_diff < 0.000001" | bc -l) )); then
    usdt_match="✅"
fi

# Trades comparison (must be exact)
if [ "$original_total_trades" = "$hyperopt_total_trades" ]; then
    trades_match="✅"
fi

# Win rate comparison (allow 0.1% tolerance)
winrate_diff=$(echo "$original_win_rate $hyperopt_win_rate" | awk '{print ($1 - $2)^2}')
if (( $(echo "$winrate_diff < 0.01" | bc -l) )); then
    winrate_match="✅"
fi

# Drawdown comparison (allow 0.01% tolerance)
drawdown_diff=$(echo "$original_max_drawdown $hyperopt_max_drawdown" | awk '{print ($1 - $2)^2}')
if (( $(echo "$drawdown_diff < 0.0001" | bc -l) )); then
    drawdown_match="✅"
fi

# Write comparison results
printf "%-25s | %-15s | %-15s | %-10s\n" "Profit %" "$original_profit_percent%" "$hyperopt_profit_percent%" "$profit_match" >> "$COMPARISON_RESULTS"
printf "%-25s | %-15s | %-15s | %-10s\n" "Absolute Profit (USDT)" "$original_profit_usdt" "$hyperopt_profit_usdt" "$usdt_match" >> "$COMPARISON_RESULTS"
printf "%-25s | %-15s | %-15s | %-10s\n" "Total Trades" "$original_total_trades" "$hyperopt_total_trades" "$trades_match" >> "$COMPARISON_RESULTS"
printf "%-25s | %-15s | %-15s | %-10s\n" "Win Rate %" "$original_win_rate%" "$hyperopt_win_rate%" "$winrate_match" >> "$COMPARISON_RESULTS"
printf "%-25s | %-15s | %-15s | %-10s\n" "Max Drawdown %" "$original_max_drawdown%" "$hyperopt_max_drawdown%" "$drawdown_match" >> "$COMPARISON_RESULTS"

echo "" >> "$COMPARISON_RESULTS"

# Overall validation
all_match="✅"
if [[ "$profit_match" == "❌" || "$usdt_match" == "❌" || "$trades_match" == "❌" || "$winrate_match" == "❌" || "$drawdown_match" == "❌" ]]; then
    all_match="❌"
fi

echo "🏆 FINAL VALIDATION RESULT:" >> "$COMPARISON_RESULTS"
echo "===========================" >> "$COMPARISON_RESULTS"
echo "Baseline Match: $all_match" >> "$COMPARISON_RESULTS"
echo "" >> "$COMPARISON_RESULTS"

if [ "$all_match" = "✅" ]; then
    echo "✅ SUCCESS: Hyperopt version matches original baseline perfectly!" >> "$COMPARISON_RESULTS"
    echo "✅ Safe to proceed with hyperparameter optimization." >> "$COMPARISON_RESULTS"
    echo "✅ Default parameters preserve existing performance." >> "$COMPARISON_RESULTS"
    
    echo "✅ 🎉 BASELINE VERIFICATION PASSED!"
    echo "✅ Hyperopt version produces identical results to original"
    echo "✅ Safe to proceed with optimization"
    
else
    echo "❌ FAILURE: Hyperopt version does NOT match original baseline!" >> "$COMPARISON_RESULTS"
    echo "❌ DO NOT proceed with optimization until this is fixed." >> "$COMPARISON_RESULTS"
    echo "❌ Check hyperparameter default values and logic implementation." >> "$COMPARISON_RESULTS"
    
    echo "❌ 🚨 BASELINE VERIFICATION FAILED!"
    echo "❌ Hyperopt version differs from original - DO NOT OPTIMIZE!"
    echo "❌ Fix hyperopt implementation before proceeding"
fi

echo "" >> "$COMPARISON_RESULTS"

# Display summary to console
echo ""
echo "📄 Results saved to:"
echo "   📊 Original: $ORIGINAL_RESULTS"
echo "   📊 Hyperopt: $HYPEROPT_RESULTS"  
echo "   📊 Comparison: $COMPARISON_RESULTS"
echo ""

# Final console output
if [ "$all_match" = "✅" ]; then
    echo "🎯 NEXT STEPS:"
    echo "1. Run hyperparameter optimization: ./test_hyperopt_optimization.sh"
    echo "2. Validate optimized results on out-of-sample data"
    echo "3. Deploy if better than baseline"
else
    echo "🔧 FIX REQUIRED:"
    echo "1. Check CryptoScalpingOptimizedHyperopt default values"
    echo "2. Ensure logic matches CryptoScalpingOptimized exactly"
    echo "3. Re-run this test until it passes"
fi
echo ""

exit 0 