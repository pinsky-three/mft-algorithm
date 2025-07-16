#!/bin/bash

# 🎯 CUSTOM PARAMETER OPTIMIZATION FRAMEWORK
# ==========================================
# Direct parameter modification and A/B testing approach
# Avoids hyperopt complexity while enabling systematic optimization

echo "🚀 CUSTOM PARAMETER OPTIMIZATION FRAMEWORK"
echo "=========================================="
echo ""
echo "🎯 APPROACH: Direct parameter modification + A/B testing"
echo "📊 BASELINE: +8.745 USDT, 254 trades, 1.457 USDT avg monthly"
echo "⚠️  CONSERVATIVE: Test small variations around proven values"
echo ""

# ===== CONFIGURATION =====

# Test period - use profitable months for training
TRAIN_TIMERANGE="20250101-20250501"  # Jan-Apr (4 months)
VALIDATION_TIMERANGE="20250501-20250601"  # May (1 month validation)

# Test pairs
PAIRS="BTC/USDT ETH/USDT SOL/USDT"
TIMEFRAME="1m"
FEE="0.0002"

# Results directory
RESULTS_DIR="parameter_optimization_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

# Strategy file paths
ORIGINAL_STRATEGY="user_data/strategies/CryptoScalpingOptimized.py"
TEST_STRATEGY="user_data/strategies/CryptoScalpingOptimizedTest.py"

echo "📅 Training Period: ${TRAIN_TIMERANGE}"
echo "📅 Validation Period: ${VALIDATION_TIMERANGE}"
echo "💰 Pairs: ${PAIRS}"
echo "📁 Results Directory: ${RESULTS_DIR}"
echo ""

# ===== PARAMETER TEST DEFINITIONS =====

# Define parameter test cases (conservative ranges around current values)
declare -A PARAMETER_TESTS=(
    # ROI Ladder Tests
    ["roi_aggressive"]="ROI_0=0.030 ROI_2=0.025 ROI_6=0.020"
    ["roi_conservative"]="ROI_0=0.020 ROI_2=0.015 ROI_6=0.010"
    ["roi_balanced"]="ROI_0=0.028 ROI_2=0.022 ROI_6=0.016"
    
    # Market Health Tests  
    ["health_relaxed"]="MIN_MARKET_HEALTH=0.4 MIN_TREND_QUALITY=0.15 MAX_CHOPPINESS=0.8"
    ["health_strict"]="MIN_MARKET_HEALTH=0.6 MIN_TREND_QUALITY=0.25 MAX_CHOPPINESS=0.6"
    ["health_moderate"]="MIN_MARKET_HEALTH=0.55 MIN_TREND_QUALITY=0.22 MAX_CHOPPINESS=0.65"
    
    # Entry Quality Tests
    ["entry_relaxed"]="MIN_VOLUME_RATIO=1.7 RSI_THRESHOLD=55 MOMENTUM_STRENGTH=0.75"
    ["entry_strict"]="MIN_VOLUME_RATIO=2.1 RSI_THRESHOLD=60 MOMENTUM_STRENGTH=0.82"
    ["entry_balanced"]="MIN_VOLUME_RATIO=2.0 RSI_THRESHOLD=58 MOMENTUM_STRENGTH=0.80"
    
    # Risk Management Tests
    ["risk_tight"]="STOPLOSS=-0.020 MIN_ATR_RATIO=0.0025"
    ["risk_loose"]="STOPLOSS=-0.030 MIN_ATR_RATIO=0.0020"
    ["risk_balanced"]="STOPLOSS=-0.027 MIN_ATR_RATIO=0.0023"
    
    # Combined Optimizations
    ["combo_aggressive"]="ROI_0=0.032 MIN_MARKET_HEALTH=0.45 MIN_VOLUME_RATIO=1.8 STOPLOSS=-0.022"
    ["combo_conservative"]="ROI_0=0.022 MIN_MARKET_HEALTH=0.55 MIN_VOLUME_RATIO=2.0 STOPLOSS=-0.028"
)

# Test descriptions for reporting
declare -A TEST_DESCRIPTIONS=(
    ["roi_aggressive"]="Higher ROI targets (3.2%/2.5%/2.0%) - faster exits"
    ["roi_conservative"]="Lower ROI targets (2.0%/1.5%/1.0%) - longer holds"
    ["roi_balanced"]="Balanced ROI targets (2.8%/2.2%/1.6%) - moderate"
    
    ["health_relaxed"]="Relaxed market filters - more opportunities"
    ["health_strict"]="Strict market filters - higher quality only"
    ["health_moderate"]="Moderate market filters - balanced approach"
    
    ["entry_relaxed"]="Relaxed entry criteria - more trades"
    ["entry_strict"]="Strict entry criteria - fewer but higher quality"
    ["entry_balanced"]="Balanced entry criteria - moderate selectivity"
    
    ["risk_tight"]="Tighter risk management - smaller losses"
    ["risk_loose"]="Looser risk management - ride more volatility"
    ["risk_balanced"]="Balanced risk management - moderate tolerance"
    
    ["combo_aggressive"]="Aggressive combo: Higher ROI + relaxed filters + tight risk"
    ["combo_conservative"]="Conservative combo: Lower ROI + strict filters + loose risk"
)

echo "🧪 PARAMETER TEST CASES:"
echo "======================="
for test_name in "${!PARAMETER_TESTS[@]}"; do
    echo "📊 ${test_name}: ${TEST_DESCRIPTIONS[$test_name]}"
done
echo ""

# ===== BASELINE REFERENCE =====

echo "🔍 ESTABLISHING BASELINE REFERENCE"
echo "=================================="

# Run baseline test to establish reference
echo "🔄 Running baseline test..."
baseline_output=$(docker compose run --rm freqtrade backtesting \
    -s CryptoScalpingOptimized \
    -p ${PAIRS} \
    --timerange ${TRAIN_TIMERANGE} \
    --fee ${FEE} \
    --timeframe ${TIMEFRAME} \
    2>/dev/null | tr -d '\r')

# Extract baseline metrics
baseline_profit=$(echo "$baseline_output" | grep "│ Total profit %" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)%[[:space:]]*│.*/\1/')
baseline_usdt=$(echo "$baseline_output" | grep "│ Absolute profit" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)[[:space:]]*USDT[[:space:]]*│.*/\1/')
baseline_trades=$(echo "$baseline_output" | grep "│ Total/Daily Avg Trades" | head -1 | sed 's/.*│[[:space:]]*\([0-9]*\)[[:space:]]*\/.*│.*/\1/')
baseline_winrate=$(echo "$baseline_output" | grep "│    TOTAL │" | head -1 | sed 's/.*│[[:space:]]*[0-9]*[[:space:]]*[0-9]*[[:space:]]*[0-9]*[[:space:]]*\([0-9.]*\)[[:space:]]*│.*/\1/')
baseline_drawdown=$(echo "$baseline_output" | grep "│ Max % of account underwater" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)%[[:space:]]*│.*/\1/')

echo "✅ BASELINE ESTABLISHED:"
echo "   Profit: ${baseline_profit}% (${baseline_usdt} USDT)"
echo "   Trades: ${baseline_trades}"  
echo "   Win Rate: ${baseline_winrate}%"
echo "   Max Drawdown: ${baseline_drawdown}%"
echo ""

# Save baseline results
baseline_file="${RESULTS_DIR}/baseline_results.txt"
echo "🎯 BASELINE RESULTS" > "$baseline_file"
echo "==================" >> "$baseline_file"
echo "Date: $(date)" >> "$baseline_file"
echo "Period: ${TRAIN_TIMERANGE}" >> "$baseline_file"
echo "Pairs: ${PAIRS}" >> "$baseline_file"
echo "" >> "$baseline_file"
echo "Profit %: ${baseline_profit}" >> "$baseline_file"
echo "Profit USDT: ${baseline_usdt}" >> "$baseline_file"
echo "Total Trades: ${baseline_trades}" >> "$baseline_file"
echo "Win Rate %: ${baseline_winrate}" >> "$baseline_file"
echo "Max Drawdown %: ${baseline_drawdown}" >> "$baseline_file"

# ===== PARAMETER TESTING FUNCTION =====

test_parameters() {
    local test_name="$1"
    local parameters="$2"
    local description="$3"
    
    echo "🔄 Testing: ${test_name}"
    echo "   Description: ${description}"
    echo "   Parameters: ${parameters}"
    
    # Create test strategy by copying original and modifying parameters
    cp "$ORIGINAL_STRATEGY" "$TEST_STRATEGY"
    
    # Apply parameter modifications
    IFS=' ' read -ra PARAM_ARRAY <<< "$parameters"
    for param in "${PARAM_ARRAY[@]}"; do
        IFS='=' read -ra PARAM_SPLIT <<< "$param"
        param_name="${PARAM_SPLIT[0]}"
        param_value="${PARAM_SPLIT[1]}"
        
        # Modify the parameter in the test strategy
        case "$param_name" in
            "ROI_0"|"ROI_2"|"ROI_6")
                # Handle ROI parameters
                if [[ "$param_name" == "ROI_0" ]]; then
                    sed -i.bak "s/\"0\": [0-9.]*/\"0\": $param_value/" "$TEST_STRATEGY"
                elif [[ "$param_name" == "ROI_2" ]]; then
                    sed -i.bak "s/\"2\": [0-9.]*/\"2\": $param_value/" "$TEST_STRATEGY"
                elif [[ "$param_name" == "ROI_6" ]]; then
                    sed -i.bak "s/\"6\": [0-9.]*/\"6\": $param_value/" "$TEST_STRATEGY"
                fi
                ;;
            "STOPLOSS")
                sed -i.bak "s/stoploss: float = [0-9.-]*/stoploss: float = $param_value/" "$TEST_STRATEGY"
                ;;
            *)
                # Handle other parameters
                sed -i.bak "s/${param_name} = [0-9.]*/${param_name} = $param_value/" "$TEST_STRATEGY"
                ;;
        esac
    done
    
    # Clean up backup files
    rm -f "${TEST_STRATEGY}.bak"
    
    # Run backtest with modified parameters
    test_output=$(docker compose run --rm freqtrade backtesting \
        -s CryptoScalpingOptimizedTest \
        -p ${PAIRS} \
        --timerange ${TRAIN_TIMERANGE} \
        --fee ${FEE} \
        --timeframe ${TIMEFRAME} \
        2>/dev/null | tr -d '\r')
    
    # Extract test metrics
    test_profit=$(echo "$test_output" | grep "│ Total profit %" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)%[[:space:]]*│.*/\1/')
    test_usdt=$(echo "$test_output" | grep "│ Absolute profit" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)[[:space:]]*USDT[[:space:]]*│.*/\1/')
    test_trades=$(echo "$test_output" | grep "│ Total/Daily Avg Trades" | head -1 | sed 's/.*│[[:space:]]*\([0-9]*\)[[:space:]]*\/.*│.*/\1/')
    test_winrate=$(echo "$test_output" | grep "│    TOTAL │" | head -1 | sed 's/.*│[[:space:]]*[0-9]*[[:space:]]*[0-9]*[[:space:]]*[0-9]*[[:space:]]*\([0-9.]*\)[[:space:]]*│.*/\1/')
    test_drawdown=$(echo "$test_output" | grep "│ Max % of account underwater" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)%[[:space:]]*│.*/\1/')
    
    # Calculate improvements
    profit_diff=$(echo "scale=2; $test_usdt - $baseline_usdt" | bc -l 2>/dev/null || echo "0")
    trade_diff=$(echo "$test_trades - $baseline_trades" | bc 2>/dev/null || echo "0")
    
    # Determine if this is an improvement
    improvement=""
    if (( $(echo "$profit_diff > 0" | bc -l) )); then
        improvement="✅ IMPROVEMENT"
    elif (( $(echo "$profit_diff < -1" | bc -l) )); then
        improvement="❌ SIGNIFICANT LOSS"
    else
        improvement="⚠️ MARGINAL"
    fi
    
    echo "   Results: ${test_profit}% (${test_usdt} USDT), ${test_trades} trades"
    echo "   vs Baseline: ${improvement} (${profit_diff:+}${profit_diff} USDT, ${trade_diff:+}${trade_diff} trades)"
    echo ""
    
    # Save test results
    test_file="${RESULTS_DIR}/test_${test_name}.txt"
    echo "🧪 TEST RESULTS: ${test_name}" > "$test_file"
    echo "================================" >> "$test_file"
    echo "Description: ${description}" >> "$test_file"
    echo "Parameters: ${parameters}" >> "$test_file"
    echo "Date: $(date)" >> "$test_file"
    echo "" >> "$test_file"
    echo "RESULTS:" >> "$test_file"
    echo "Profit %: ${test_profit}" >> "$test_file"
    echo "Profit USDT: ${test_usdt}" >> "$test_file"
    echo "Total Trades: ${test_trades}" >> "$test_file"
    echo "Win Rate %: ${test_winrate}" >> "$test_file"
    echo "Max Drawdown %: ${test_drawdown}" >> "$test_file"
    echo "" >> "$test_file"
    echo "vs BASELINE:" >> "$test_file"
    echo "Profit Diff: ${profit_diff:+}${profit_diff} USDT" >> "$test_file"
    echo "Trade Diff: ${trade_diff:+}${trade_diff} trades" >> "$test_file"
    echo "Assessment: ${improvement}" >> "$test_file"
    
    # Return improvement status for tracking
    echo "$improvement|$profit_diff|$test_name|$test_usdt|$test_trades|$test_winrate"
}

# ===== RUN ALL PARAMETER TESTS =====

echo "🚀 RUNNING PARAMETER OPTIMIZATION TESTS"
echo "======================================="
echo ""

best_improvement=""
best_profit_diff=0
best_test_name=""
all_results=()

# Run all parameter tests
for test_name in "${!PARAMETER_TESTS[@]}"; do
    parameters="${PARAMETER_TESTS[$test_name]}"
    description="${TEST_DESCRIPTIONS[$test_name]}"
    
    result=$(test_parameters "$test_name" "$parameters" "$description")
    all_results+=("$result")
    
    # Track best improvement
    profit_diff=$(echo "$result" | cut -d'|' -f2)
    if (( $(echo "$profit_diff > $best_profit_diff" | bc -l) )); then
        best_profit_diff="$profit_diff"
        best_test_name="$test_name"
        best_improvement="$result"
    fi
done

# Clean up test strategy
rm -f "$TEST_STRATEGY"

# ===== RESULTS SUMMARY =====

echo "🏆 OPTIMIZATION RESULTS SUMMARY"
echo "==============================="
echo ""

# Sort results by profit difference
IFS=$'\n' sorted_results=($(printf '%s\n' "${all_results[@]}" | sort -t'|' -k2 -nr))

echo "📊 ALL TESTS RANKED BY PERFORMANCE:"
echo "=================================="
rank=1
for result in "${sorted_results[@]}"; do
    IFS='|' read -ra RESULT_PARTS <<< "$result"
    improvement="${RESULT_PARTS[0]}"
    profit_diff="${RESULT_PARTS[1]}"
    test_name="${RESULT_PARTS[2]}"
    test_usdt="${RESULT_PARTS[3]}"
    test_trades="${RESULT_PARTS[4]}"
    test_winrate="${RESULT_PARTS[5]}"
    
    description="${TEST_DESCRIPTIONS[$test_name]}"
    
    printf "%2d. %-20s %s (%+.3f USDT) - %s\n" \
        "$rank" "$test_name" "$improvement" "$profit_diff" "$description"
    
    rank=$((rank + 1))
done

echo ""

# Best result details
if [[ -n "$best_test_name" ]]; then
    echo "🥇 BEST PERFORMING TEST:"
    echo "======================"
    echo "Test: $best_test_name"
    echo "Description: ${TEST_DESCRIPTIONS[$best_test_name]}"
    echo "Parameters: ${PARAMETER_TESTS[$best_test_name]}"
    echo "Improvement: +${best_profit_diff} USDT vs baseline"
    echo ""
    
    # Save best result
    best_file="${RESULTS_DIR}/BEST_RESULT.txt"
    echo "🏆 BEST OPTIMIZATION RESULT" > "$best_file"
    echo "===========================" >> "$best_file"
    echo "Test Name: $best_test_name" >> "$best_file"
    echo "Description: ${TEST_DESCRIPTIONS[$best_test_name]}" >> "$best_file"
    echo "Parameters: ${PARAMETER_TESTS[$best_test_name]}" >> "$best_file"
    echo "Improvement: +${best_profit_diff} USDT" >> "$best_file"
    echo "Date: $(date)" >> "$best_file"
else
    echo "❌ No improvements found over baseline"
fi

# ===== VALIDATION TEST =====

if [[ -n "$best_test_name" ]] && (( $(echo "$best_profit_diff > 0.5" | bc -l) )); then
    echo "🧪 OUT-OF-SAMPLE VALIDATION"
    echo "=========================="
    echo ""
    echo "🔄 Testing best parameters on validation period: ${VALIDATION_TIMERANGE}"
    
    # Create validation strategy with best parameters
    cp "$ORIGINAL_STRATEGY" "$TEST_STRATEGY"
    parameters="${PARAMETER_TESTS[$best_test_name]}"
    
    # Apply best parameters (same logic as test_parameters function)
    IFS=' ' read -ra PARAM_ARRAY <<< "$parameters"
    for param in "${PARAM_ARRAY[@]}"; do
        IFS='=' read -ra PARAM_SPLIT <<< "$param"
        param_name="${PARAM_SPLIT[0]}"
        param_value="${PARAM_SPLIT[1]}"
        
        case "$param_name" in
            "ROI_0"|"ROI_2"|"ROI_6")
                if [[ "$param_name" == "ROI_0" ]]; then
                    sed -i.bak "s/\"0\": [0-9.]*/\"0\": $param_value/" "$TEST_STRATEGY"
                elif [[ "$param_name" == "ROI_2" ]]; then
                    sed -i.bak "s/\"2\": [0-9.]*/\"2\": $param_value/" "$TEST_STRATEGY"
                elif [[ "$param_name" == "ROI_6" ]]; then
                    sed -i.bak "s/\"6\": [0-9.]*/\"6\": $param_value/" "$TEST_STRATEGY"
                fi
                ;;
            "STOPLOSS")
                sed -i.bak "s/stoploss: float = [0-9.-]*/stoploss: float = $param_value/" "$TEST_STRATEGY"
                ;;
            *)
                sed -i.bak "s/${param_name} = [0-9.]*/${param_name} = $param_value/" "$TEST_STRATEGY"
                ;;
        esac
    done
    rm -f "${TEST_STRATEGY}.bak"
    
    # Run validation test
    validation_output=$(docker compose run --rm freqtrade backtesting \
        -s CryptoScalpingOptimizedTest \
        -p ${PAIRS} \
        --timerange ${VALIDATION_TIMERANGE} \
        --fee ${FEE} \
        --timeframe ${TIMEFRAME} \
        2>/dev/null | tr -d '\r')
    
    # Extract validation metrics  
    val_profit=$(echo "$validation_output" | grep "│ Total profit %" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)%[[:space:]]*│.*/\1/')
    val_usdt=$(echo "$validation_output" | grep "│ Absolute profit" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)[[:space:]]*USDT[[:space:]]*│.*/\1/')
    val_trades=$(echo "$validation_output" | grep "│ Total/Daily Avg Trades" | head -1 | sed 's/.*│[[:space:]]*\([0-9]*\)[[:space:]]*\/.*│.*/\1/')
    val_winrate=$(echo "$validation_output" | grep "│    TOTAL │" | head -1 | sed 's/.*│[[:space:]]*[0-9]*[[:space:]]*[0-9]*[[:space:]]*[0-9]*[[:space:]]*\([0-9.]*\)[[:space:]]*│.*/\1/')
    
    echo "✅ VALIDATION RESULTS:"
    echo "   Profit: ${val_profit}% (${val_usdt} USDT)"
    echo "   Trades: ${val_trades}"
    echo "   Win Rate: ${val_winrate}%"
    echo ""
    
    # Compare to baseline May performance (known: 0.30% / 2.975 USDT)
    baseline_may_usdt="2.975"
    val_improvement=$(echo "scale=3; $val_usdt - $baseline_may_usdt" | bc -l 2>/dev/null || echo "0")
    
    if (( $(echo "$val_improvement > 0" | bc -l) )); then
        echo "🎉 VALIDATION SUCCESS: +${val_improvement} USDT vs baseline May"
        echo "✅ Optimized parameters perform better on unseen data"
    else
        echo "⚠️ VALIDATION CONCERN: ${val_improvement} USDT vs baseline May"
        echo "❌ May indicate overfitting to training period"
    fi
    
    # Save validation results
    validation_file="${RESULTS_DIR}/validation_results.txt"
    echo "🧪 VALIDATION RESULTS" > "$validation_file"
    echo "===================" >> "$validation_file"
    echo "Best Test: $best_test_name" >> "$validation_file"
    echo "Parameters: ${PARAMETER_TESTS[$best_test_name]}" >> "$validation_file"
    echo "Period: ${VALIDATION_TIMERANGE}" >> "$validation_file"
    echo "" >> "$validation_file"
    echo "Profit %: ${val_profit}" >> "$validation_file"
    echo "Profit USDT: ${val_usdt}" >> "$validation_file"
    echo "Total Trades: ${val_trades}" >> "$validation_file"
    echo "Win Rate %: ${val_winrate}" >> "$validation_file"
    echo "" >> "$validation_file"
    echo "vs Baseline May: ${val_improvement:+}${val_improvement} USDT" >> "$validation_file"
    
    # Clean up
    rm -f "$TEST_STRATEGY"
else
    echo "⏭️ SKIPPING VALIDATION: No significant improvement found"
fi

# ===== FINAL REPORT =====

echo ""
echo "📄 OPTIMIZATION COMPLETE"
echo "========================"
echo ""
echo "📁 Results Directory: ${RESULTS_DIR}/"
echo "📊 Files Generated:"
ls -la "$RESULTS_DIR/"
echo ""

echo "🎯 NEXT STEPS:"
if [[ -n "$best_test_name" ]] && (( $(echo "$best_profit_diff > 0.5" | bc -l) )); then
    echo "1. ✅ Significant improvement found: $best_test_name (+${best_profit_diff} USDT)"
    echo "2. 📝 Review parameters: ${PARAMETER_TESTS[$best_test_name]}"
    echo "3. 🔄 Apply best parameters to production strategy"
    echo "4. 🧪 Run full 6-month backtest for final validation"
    echo "5. 🚀 Deploy if consistently better than baseline"
else
    echo "1. ⚠️ No significant improvements found with current parameter ranges"
    echo "2. 🔄 Consider testing wider parameter ranges"
    echo "3. 📊 Analyze individual parameter impacts for insights"
    echo "4. 🎯 Focus on parameters showing marginal improvements"
    echo "5. 📈 Current strategy (+8.745 USDT) may already be well-optimized"
fi

echo ""
echo "⚠️ IMPORTANT REMINDER:"
echo "Only deploy parameter changes that show CONSISTENT improvement"
echo "across both training and validation periods!"
echo ""

echo "🏁 Parameter optimization framework complete!"

exit 0 