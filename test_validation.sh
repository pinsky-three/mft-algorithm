#!/bin/bash

# 🧪 VALIDATION & COMBINATION TESTING
# ===================================
# Test best parameters on validation data (May 2025)

echo "🧪 VALIDATION & COMBINATION TESTING"
echo "==================================="
echo ""

TRAIN_TIMERANGE="20250101-20250501"  # Training period
VALIDATION_TIMERANGE="20250501-20250601"  # May 2025 validation
PAIRS="BTC/USDT ETH/USDT SOL/USDT"
ORIGINAL_STRATEGY="user_data/strategies/CryptoScalpingOptimized.py"

echo "📊 Training: ${TRAIN_TIMERANGE}"
echo "🧪 Validation: ${VALIDATION_TIMERANGE}"
echo "💰 Pairs: ${PAIRS}"
echo ""

# ===== BASELINE VALIDATION =====
echo "🔍 BASELINE VALIDATION TEST"
echo "=========================="

val_baseline_output=$(docker compose run --rm freqtrade backtesting \
    -s CryptoScalpingOptimized \
    -p ${PAIRS} \
    --timerange ${VALIDATION_TIMERANGE} \
    --fee 0.0002 \
    --timeframe 1m \
    2>/dev/null)

val_baseline_profit=$(echo "$val_baseline_output" | grep "│ Total profit %" | head -1 | awk -F'│' '{print $3}' | tr -d ' %')
val_baseline_usdt=$(echo "$val_baseline_output" | grep "│ Absolute profit" | head -1 | awk -F'│' '{print $3}' | tr -d ' USDT')
val_baseline_trades=$(echo "$val_baseline_output" | grep "│ Total/Daily Avg Trades" | head -1 | awk -F'│' '{print $3}' | awk '{print $1}')

echo "✅ BASELINE MAY: ${val_baseline_profit}% (${val_baseline_usdt} USDT), ${val_baseline_trades} trades"
echo ""

# ===== VALIDATION TEST FUNCTION =====
test_validation() {
    local test_name="$1"
    local description="$2"
    shift 2
    local modifications=("$@")
    
    echo "🔄 Validating: ${test_name}"
    echo "   ${description}"
    
    # Create test strategy
    cp "$ORIGINAL_STRATEGY" "user_data/strategies/TestStrategy.py"
    sed -i.bak 's/class CryptoScalpingOptimized/class TestStrategy/' "user_data/strategies/TestStrategy.py"
    
    # Apply modifications
    for mod in "${modifications[@]}"; do
        case "$mod" in
            "volume_strict")
                sed -i.bak 's/MIN_VOLUME_RATIO = 1.9/MIN_VOLUME_RATIO = 2.1/' "user_data/strategies/TestStrategy.py"
                ;;
            "roi_conservative")
                sed -i.bak 's/"0": 0.025/"0": 0.020/' "user_data/strategies/TestStrategy.py"
                sed -i.bak 's/"2": 0.020/"2": 0.015/' "user_data/strategies/TestStrategy.py"
                sed -i.bak 's/"6": 0.015/"6": 0.010/' "user_data/strategies/TestStrategy.py"
                ;;
            "roi_aggressive")
                sed -i.bak 's/"0": 0.025/"0": 0.030/' "user_data/strategies/TestStrategy.py"
                sed -i.bak 's/"2": 0.020/"2": 0.025/' "user_data/strategies/TestStrategy.py"
                sed -i.bak 's/"6": 0.015/"6": 0.020/' "user_data/strategies/TestStrategy.py"
                ;;
        esac
    done
    
    rm -f "user_data/strategies/TestStrategy.py.bak"
    
    # Run validation test
    val_output=$(docker compose run --rm freqtrade backtesting \
        -s TestStrategy \
        -p ${PAIRS} \
        --timerange ${VALIDATION_TIMERANGE} \
        --fee 0.0002 \
        --timeframe 1m \
        2>/dev/null)
    
    # Extract validation results
    val_profit=$(echo "$val_output" | grep "│ Total profit %" | head -1 | awk -F'│' '{print $3}' | tr -d ' %')
    val_usdt=$(echo "$val_output" | grep "│ Absolute profit" | head -1 | awk -F'│' '{print $3}' | tr -d ' USDT')
    val_trades=$(echo "$val_output" | grep "│ Total/Daily Avg Trades" | head -1 | awk -F'│' '{print $3}' | awk '{print $1}')
    val_winrate=$(echo "$val_output" | grep "│    TOTAL │" | head -1 | awk -F'│' '{print $5}' | tr -d ' ')
    
    # Calculate validation improvement
    if [[ -n "$val_usdt" && -n "$val_baseline_usdt" ]]; then
        val_diff=$(echo "scale=3; $val_usdt - $val_baseline_usdt" | bc -l 2>/dev/null || echo "0")
    else
        val_diff="0"
    fi
    
    # Status
    if (( $(echo "$val_diff > 0.5" | bc -l 2>/dev/null) )); then
        val_status="✅ VALIDATION SUCCESS"
    elif (( $(echo "$val_diff > 0" | bc -l 2>/dev/null) )); then
        val_status="🟡 MARGINAL IMPROVEMENT"
    elif (( $(echo "$val_diff < -0.5" | bc -l 2>/dev/null) )); then
        val_status="❌ VALIDATION FAILURE"
    else
        val_status="⚪ NEUTRAL"
    fi
    
    echo "   Result: ${val_profit}% (${val_usdt} USDT), ${val_trades} trades, ${val_winrate}% win rate"
    echo "   vs Baseline May: ${val_status} (${val_diff:+}${val_diff} USDT)"
    echo ""
    
    # Save results
    echo "${test_name}|${val_diff}|${val_usdt}|${val_trades}|${val_winrate}|${val_status}" >> "validation_results.txt"
    
    # Clean up
    rm -f "user_data/strategies/TestStrategy.py"
    
    return 0
}

# ===== RUN VALIDATION TESTS =====
echo "🧪 VALIDATION TESTS"
echo "=================="
echo ""

# Initialize results
echo "# Validation Results (May 2025)" > "validation_results.txt"
echo "test_name|val_diff|usdt|trades|winrate|status" >> "validation_results.txt"

# Test 1: Volume Strict (Best individual performer)
test_validation "volume_strict" "Higher volume threshold: 2.1x" "volume_strict"

# Test 2: ROI Conservative (Second best performer)
test_validation "roi_conservative" "Lower ROI targets: 2.0%/1.5%/1.0%" "roi_conservative"

# Test 3: ROI Aggressive (Marginal performer)
test_validation "roi_aggressive" "Higher ROI targets: 3.0%/2.5%/2.0%" "roi_aggressive"

# Test 4: Combined Best (Volume Strict + ROI Conservative)
test_validation "combo_best" "Volume 2.1x + ROI Conservative" "volume_strict" "roi_conservative"

# Test 5: Combined Alternative (Volume Strict + ROI Aggressive)
test_validation "combo_alt" "Volume 2.1x + ROI Aggressive" "volume_strict" "roi_aggressive"

# ===== ANALYZE VALIDATION RESULTS =====
echo "📊 VALIDATION ANALYSIS"
echo "====================="
echo ""

if [[ -f "validation_results.txt" ]]; then
    # Sort by validation difference
    tail -n +3 "validation_results.txt" | sort -t'|' -k2 -nr > "sorted_validation.txt"
    
    echo "🏆 VALIDATION RANKINGS:"
    echo "======================"
    rank=1
    while IFS='|' read -r test_name val_diff usdt trades winrate status; do
        printf "%2d. %-18s %s (%+.3f USDT)\n" \
            "$rank" "$test_name" "$status" "$val_diff"
        printf "    May: %s USDT, %s trades, %s%% win rate\n" "$usdt" "$trades" "$winrate"
        rank=$((rank + 1))
        echo ""
    done < "sorted_validation.txt"
    
    # Best validation result
    best_val_line=$(head -1 "sorted_validation.txt")
    IFS='|' read -r best_val_test best_val_diff best_val_usdt best_val_trades best_val_winrate best_val_status <<< "$best_val_line"
    
    echo "🎯 VALIDATION SUMMARY"
    echo "===================="
    echo ""
    
    if (( $(echo "$best_val_diff > 0.5" | bc -l 2>/dev/null) )); then
        echo "🎉 VALIDATION SUCCESS!"
        echo "   Best: $best_val_test"
        echo "   May Improvement: +${best_val_diff} USDT"
        echo "   May Performance: ${best_val_usdt} USDT with ${best_val_trades} trades"
        echo ""
        echo "🚀 RECOMMENDATION:"
        echo "   Apply these parameters to production strategy"
        echo "   Expected 6-month performance improvement based on validation"
    elif (( $(echo "$best_val_diff > 0" | bc -l 2>/dev/null) )); then
        echo "🟡 MARGINAL VALIDATION"
        echo "   Best: $best_val_test (+${best_val_diff} USDT)"
        echo "   Consider deployment with caution"
    else
        echo "⚠️ VALIDATION CONCERNS"
        echo "   No parameters improved validation performance"
        echo "   May indicate overfitting to training period"
        echo "   Consider keeping current strategy"
    fi
    
    # Compare to known baseline May performance (2.975 USDT from monthly results)
    echo ""
    echo "📊 BASELINE COMPARISON:"
    echo "   Current May baseline: ${val_baseline_usdt} USDT"
    echo "   Known monthly result: 2.975 USDT"
    if [[ -n "$best_val_usdt" ]]; then
        known_baseline="2.975"
        improvement_vs_known=$(echo "scale=3; $best_val_usdt - $known_baseline" | bc -l 2>/dev/null || echo "0")
        echo "   Best optimized May: ${best_val_usdt} USDT (${improvement_vs_known:+}${improvement_vs_known} vs known)"
    fi
    
else
    echo "❌ No validation results found"
fi

# ===== FINAL RECOMMENDATIONS =====
echo ""
echo "🎯 FINAL RECOMMENDATIONS"
echo "======================="
echo ""

if (( $(echo "$best_val_diff > 0.5" | bc -l 2>/dev/null) )); then
    echo "✅ DEPLOY RECOMMENDATION: $best_val_test"
    echo ""
    echo "📋 DEPLOYMENT STEPS:"
    echo "1. Apply parameters to CryptoScalpingOptimized.py"
    echo "2. Run full 6-month backtest for final confirmation"
    echo "3. Test in paper trading for 1-2 weeks"
    echo "4. Deploy to live trading with small position size"
    echo "5. Monitor performance vs baseline"
    echo ""
    echo "📊 EXPECTED PERFORMANCE:"
    if [[ "$best_val_test" == "volume_strict" ]]; then
        echo "   Training improvement: +5.185 USDT (+61%)"
        echo "   Parameter: MIN_VOLUME_RATIO = 2.1 (was 1.9)"
        echo "   Effect: Higher quality trades, premium liquidity only"
    elif [[ "$best_val_test" == "combo_best" ]]; then
        echo "   Training: Volume strict + ROI conservative"
        echo "   Parameters: MIN_VOLUME_RATIO = 2.1, ROI = 2.0%/1.5%/1.0%"
        echo "   Effect: Premium liquidity + longer hold times"
    fi
else
    echo "⚠️ HOLD RECOMMENDATION"
    echo ""
    echo "🎯 ANALYSIS:"
    echo "1. Current strategy (+8.745 USDT) performs well"
    echo "2. Parameter optimizations may be overfit to training data"
    echo "3. Conservative approach: Keep current proven strategy"
    echo "4. Consider testing wider parameter ranges or different time periods"
fi

echo ""
echo "📁 Results saved to: validation_results.txt"
echo "🏁 Validation testing complete!"

exit 0 