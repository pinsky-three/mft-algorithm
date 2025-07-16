#!/bin/bash

# 🎯 SIMPLIFIED PARAMETER OPTIMIZATION FRAMEWORK
# ===============================================
# Direct parameter modification with focused A/B testing
# Compatible with macOS bash - avoids associative arrays

echo "🚀 PARAMETER OPTIMIZATION FRAMEWORK v2"
echo "======================================"
echo ""
echo "🎯 APPROACH: Focused parameter testing on high-impact variables"
echo "📊 BASELINE: +8.745 USDT, 254 trades, 1.457 USDT avg monthly"
echo ""

# ===== CONFIGURATION =====
TRAIN_TIMERANGE="20250101-20250501"  # 4 profitable months
VALIDATION_TIMERANGE="20250501-20250601"  # May validation
PAIRS="BTC/USDT ETH/USDT SOL/USDT"
TIMEFRAME="1m"
FEE="0.0002"

RESULTS_DIR="param_opt_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

ORIGINAL_STRATEGY="user_data/strategies/CryptoScalpingOptimized.py"
TEST_STRATEGY="user_data/strategies/CryptoScalpingOptimizedTest.py"

echo "📅 Training: ${TRAIN_TIMERANGE} | Validation: ${VALIDATION_TIMERANGE}"
echo "📁 Results: ${RESULTS_DIR}"
echo ""

# ===== ESTABLISH BASELINE =====
echo "🔍 ESTABLISHING BASELINE"
echo "======================="

baseline_output=$(docker compose run --rm freqtrade backtesting \
    -s CryptoScalpingOptimized \
    -p ${PAIRS} \
    --timerange ${TRAIN_TIMERANGE} \
    --fee ${FEE} \
    --timeframe ${TIMEFRAME} \
    2>/dev/null | tr -d '\r')

baseline_profit=$(echo "$baseline_output" | grep "│ Total profit %" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)%[[:space:]]*│.*/\1/')
baseline_usdt=$(echo "$baseline_output" | grep "│ Absolute profit" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)[[:space:]]*USDT[[:space:]]*│.*/\1/')
baseline_trades=$(echo "$baseline_output" | grep "│ Total/Daily Avg Trades" | head -1 | sed 's/.*│[[:space:]]*\([0-9]*\)[[:space:]]*\/.*│.*/\1/')
baseline_winrate=$(echo "$baseline_output" | grep "│    TOTAL │" | head -1 | sed 's/.*│[[:space:]]*[0-9]*[[:space:]]*[0-9]*[[:space:]]*[0-9]*[[:space:]]*\([0-9.]*\)[[:space:]]*│.*/\1/')

echo "✅ BASELINE: ${baseline_profit}% (${baseline_usdt} USDT), ${baseline_trades} trades, ${baseline_winrate}% win rate"
echo ""

# ===== PARAMETER TESTING FUNCTION =====
test_parameter_set() {
    local test_name="$1"
    local description="$2"
    shift 2
    local modifications=("$@")
    
    echo "🔄 Testing: ${test_name}"
    echo "   ${description}"
    
    # Copy original strategy
    cp "$ORIGINAL_STRATEGY" "$TEST_STRATEGY"
    
    # Apply modifications
    for mod in "${modifications[@]}"; do
        if [[ "$mod" == *"ROI"* ]]; then
            # Handle ROI modifications
            if [[ "$mod" == *"aggressive"* ]]; then
                sed -i.bak 's/"0": 0.025/"0": 0.030/' "$TEST_STRATEGY"
                sed -i.bak 's/"2": 0.020/"2": 0.025/' "$TEST_STRATEGY"
                sed -i.bak 's/"6": 0.015/"6": 0.020/' "$TEST_STRATEGY"
            elif [[ "$mod" == *"conservative"* ]]; then
                sed -i.bak 's/"0": 0.025/"0": 0.020/' "$TEST_STRATEGY"
                sed -i.bak 's/"2": 0.020/"2": 0.015/' "$TEST_STRATEGY"
                sed -i.bak 's/"6": 0.015/"6": 0.010/' "$TEST_STRATEGY"
            fi
        elif [[ "$mod" == *"health_relaxed"* ]]; then
            sed -i.bak 's/MIN_MARKET_HEALTH = 0.5/MIN_MARKET_HEALTH = 0.4/' "$TEST_STRATEGY"
            sed -i.bak 's/MIN_TREND_QUALITY = 0.2/MIN_TREND_QUALITY = 0.15/' "$TEST_STRATEGY"
            sed -i.bak 's/MAX_CHOPPINESS = 0.7/MAX_CHOPPINESS = 0.8/' "$TEST_STRATEGY"
        elif [[ "$mod" == *"health_strict"* ]]; then
            sed -i.bak 's/MIN_MARKET_HEALTH = 0.5/MIN_MARKET_HEALTH = 0.6/' "$TEST_STRATEGY"
            sed -i.bak 's/MIN_TREND_QUALITY = 0.2/MIN_TREND_QUALITY = 0.25/' "$TEST_STRATEGY"
            sed -i.bak 's/MAX_CHOPPINESS = 0.7/MAX_CHOPPINESS = 0.6/' "$TEST_STRATEGY"
        elif [[ "$mod" == *"volume_relaxed"* ]]; then
            sed -i.bak 's/MIN_VOLUME_RATIO = 1.9/MIN_VOLUME_RATIO = 1.7/' "$TEST_STRATEGY"
        elif [[ "$mod" == *"volume_strict"* ]]; then
            sed -i.bak 's/MIN_VOLUME_RATIO = 1.9/MIN_VOLUME_RATIO = 2.1/' "$TEST_STRATEGY"
        elif [[ "$mod" == *"risk_tight"* ]]; then
            sed -i.bak 's/stoploss: float = -0.025/stoploss: float = -0.020/' "$TEST_STRATEGY"
        elif [[ "$mod" == *"risk_loose"* ]]; then
            sed -i.bak 's/stoploss: float = -0.025/stoploss: float = -0.030/' "$TEST_STRATEGY"
        fi
    done
    
    # Clean backup files
    rm -f "${TEST_STRATEGY}.bak"
    
    # Run test
    test_output=$(docker compose run --rm freqtrade backtesting \
        -s CryptoScalpingOptimizedTest \
        -p ${PAIRS} \
        --timerange ${TRAIN_TIMERANGE} \
        --fee ${FEE} \
        --timeframe ${TIMEFRAME} \
        2>/dev/null | tr -d '\r')
    
    # Extract metrics
    test_profit=$(echo "$test_output" | grep "│ Total profit %" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)%[[:space:]]*│.*/\1/')
    test_usdt=$(echo "$test_output" | grep "│ Absolute profit" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)[[:space:]]*USDT[[:space:]]*│.*/\1/')
    test_trades=$(echo "$test_output" | grep "│ Total/Daily Avg Trades" | head -1 | sed 's/.*│[[:space:]]*\([0-9]*\)[[:space:]]*\/.*│.*/\1/')
    test_winrate=$(echo "$test_output" | grep "│    TOTAL │" | head -1 | sed 's/.*│[[:space:]]*[0-9]*[[:space:]]*[0-9]*[[:space:]]*[0-9]*[[:space:]]*\([0-9.]*\)[[:space:]]*│.*/\1/')
    
    # Calculate difference
    if [[ -n "$test_usdt" && -n "$baseline_usdt" ]]; then
        profit_diff=$(echo "scale=3; $test_usdt - $baseline_usdt" | bc -l 2>/dev/null || echo "0")
    else
        profit_diff="0"
    fi
    
    # Determine status
    if (( $(echo "$profit_diff > 1.0" | bc -l 2>/dev/null) )); then
        status="✅ SIGNIFICANT IMPROVEMENT"
    elif (( $(echo "$profit_diff > 0.2" | bc -l 2>/dev/null) )); then
        status="🟡 MARGINAL IMPROVEMENT"
    elif (( $(echo "$profit_diff < -1.0" | bc -l 2>/dev/null) )); then
        status="❌ SIGNIFICANT LOSS"
    else
        status="⚪ NEUTRAL"
    fi
    
    echo "   Result: ${test_profit}% (${test_usdt} USDT), ${test_trades} trades"
    echo "   vs Baseline: ${status} (${profit_diff:+}${profit_diff} USDT)"
    echo ""
    
    # Save results
    echo "$test_name|$profit_diff|$test_usdt|$test_trades|$status|$description" >> "${RESULTS_DIR}/all_results.txt"
    
    return 0
}

# ===== RUN PARAMETER TESTS =====
echo "🧪 RUNNING PARAMETER TESTS"
echo "=========================="
echo ""

# Initialize results file
echo "# Test Results" > "${RESULTS_DIR}/all_results.txt"

# Test 1: ROI Variations
test_parameter_set "roi_aggressive" "Higher ROI targets (3.0%/2.5%/2.0%) - faster exits" "roi_aggressive"
test_parameter_set "roi_conservative" "Lower ROI targets (2.0%/1.5%/1.0%) - longer holds" "roi_conservative"

# Test 2: Market Health Variations  
test_parameter_set "health_relaxed" "Relaxed market filters (0.4/0.15/0.8) - more opportunities" "health_relaxed"
test_parameter_set "health_strict" "Strict market filters (0.6/0.25/0.6) - higher quality only" "health_strict"

# Test 3: Volume Threshold Variations
test_parameter_set "volume_relaxed" "Lower volume threshold (1.7x) - more trades" "volume_relaxed"
test_parameter_set "volume_strict" "Higher volume threshold (2.1x) - premium liquidity only" "volume_strict"

# Test 4: Risk Management Variations
test_parameter_set "risk_tight" "Tighter stop loss (-2.0%) - smaller losses" "risk_tight"
test_parameter_set "risk_loose" "Looser stop loss (-3.0%) - ride more volatility" "risk_loose"

# Test 5: Combined Optimizations
test_parameter_set "combo_aggressive" "Aggressive combo: Higher ROI + Relaxed health + Tight risk" "roi_aggressive" "health_relaxed" "risk_tight"
test_parameter_set "combo_balanced" "Balanced combo: Conservative ROI + Strict health + Loose risk" "roi_conservative" "health_strict" "risk_loose"

# Clean up test strategy
rm -f "$TEST_STRATEGY"

# ===== ANALYZE RESULTS =====
echo "📊 RESULTS ANALYSIS"
echo "=================="
echo ""

if [[ -f "${RESULTS_DIR}/all_results.txt" ]]; then
    # Sort results by profit difference
    tail -n +2 "${RESULTS_DIR}/all_results.txt" | sort -t'|' -k2 -nr > "${RESULTS_DIR}/sorted_results.txt"
    
    echo "🏆 RANKED RESULTS (Best to Worst):"
    echo "=================================="
    
    rank=1
    best_test=""
    best_profit=0
    
    while IFS='|' read -r test_name profit_diff test_usdt test_trades status description; do
        printf "%2d. %-18s %s (%+.3f USDT)\n" "$rank" "$test_name" "$status" "$profit_diff"
        printf "    %s\n" "$description"
        
        if [[ $rank -eq 1 ]]; then
            best_test="$test_name"
            best_profit="$profit_diff"
        fi
        
        rank=$((rank + 1))
        echo ""
    done < "${RESULTS_DIR}/sorted_results.txt"
    
    # ===== VALIDATION TEST =====
    if (( $(echo "$best_profit > 0.5" | bc -l 2>/dev/null) )); then
        echo "🧪 VALIDATION TEST"
        echo "================="
        echo ""
        echo "🔄 Testing best configuration ($best_test) on validation period..."
        
        # Re-create best strategy for validation
        cp "$ORIGINAL_STRATEGY" "$TEST_STRATEGY"
        
        # Apply best modifications based on test name
        case "$best_test" in
            *"roi_aggressive"*) 
                sed -i.bak 's/"0": 0.025/"0": 0.030/' "$TEST_STRATEGY"
                sed -i.bak 's/"2": 0.020/"2": 0.025/' "$TEST_STRATEGY"
                sed -i.bak 's/"6": 0.015/"6": 0.020/' "$TEST_STRATEGY"
                ;;
            *"roi_conservative"*)
                sed -i.bak 's/"0": 0.025/"0": 0.020/' "$TEST_STRATEGY"
                sed -i.bak 's/"2": 0.020/"2": 0.015/' "$TEST_STRATEGY"
                sed -i.bak 's/"6": 0.015/"6": 0.010/' "$TEST_STRATEGY"
                ;;
        esac
        
        if [[ "$best_test" == *"health_relaxed"* ]]; then
            sed -i.bak 's/MIN_MARKET_HEALTH = 0.5/MIN_MARKET_HEALTH = 0.4/' "$TEST_STRATEGY"
            sed -i.bak 's/MIN_TREND_QUALITY = 0.2/MIN_TREND_QUALITY = 0.15/' "$TEST_STRATEGY"
            sed -i.bak 's/MAX_CHOPPINESS = 0.7/MAX_CHOPPINESS = 0.8/' "$TEST_STRATEGY"
        elif [[ "$best_test" == *"health_strict"* ]]; then
            sed -i.bak 's/MIN_MARKET_HEALTH = 0.5/MIN_MARKET_HEALTH = 0.6/' "$TEST_STRATEGY"
            sed -i.bak 's/MIN_TREND_QUALITY = 0.2/MIN_TREND_QUALITY = 0.25/' "$TEST_STRATEGY"
            sed -i.bak 's/MAX_CHOPPINESS = 0.7/MAX_CHOPPINESS = 0.6/' "$TEST_STRATEGY"
        fi
        
        if [[ "$best_test" == *"risk_tight"* ]]; then
            sed -i.bak 's/stoploss: float = -0.025/stoploss: float = -0.020/' "$TEST_STRATEGY"
        elif [[ "$best_test" == *"risk_loose"* ]]; then
            sed -i.bak 's/stoploss: float = -0.025/stoploss: float = -0.030/' "$TEST_STRATEGY"
        fi
        
        rm -f "${TEST_STRATEGY}.bak"
        
        # Run validation
        val_output=$(docker compose run --rm freqtrade backtesting \
            -s CryptoScalpingOptimizedTest \
            -p ${PAIRS} \
            --timerange ${VALIDATION_TIMERANGE} \
            --fee ${FEE} \
            --timeframe ${TIMEFRAME} \
            2>/dev/null | tr -d '\r')
        
        val_profit=$(echo "$val_output" | grep "│ Total profit %" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)%[[:space:]]*│.*/\1/')
        val_usdt=$(echo "$val_output" | grep "│ Absolute profit" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)[[:space:]]*USDT[[:space:]]*│.*/\1/')
        val_trades=$(echo "$val_output" | grep "│ Total/Daily Avg Trades" | head -1 | sed 's/.*│[[:space:]]*\([0-9]*\)[[:space:]]*\/.*│.*/\1/')
        val_winrate=$(echo "$val_output" | grep "│    TOTAL │" | head -1 | sed 's/.*│[[:space:]]*[0-9]*[[:space:]]*[0-9]*[[:space:]]*[0-9]*[[:space:]]*\([0-9.]*\)[[:space:]]*│.*/\1/')
        
        # Compare to baseline May (2.975 USDT from monthly results)
        baseline_may="2.975"
        val_improvement=$(echo "scale=3; $val_usdt - $baseline_may" | bc -l 2>/dev/null || echo "0")
        
        echo "✅ VALIDATION RESULTS:"
        echo "   Best Config: $best_test"
        echo "   May Results: ${val_profit}% (${val_usdt} USDT), ${val_trades} trades"
        echo "   vs Baseline May: ${val_improvement:+}${val_improvement} USDT"
        
        if (( $(echo "$val_improvement > 0" | bc -l 2>/dev/null) )); then
            echo "   🎉 VALIDATION SUCCESS: Improvement confirmed on unseen data!"
        else
            echo "   ⚠️ VALIDATION CONCERN: May indicate overfitting"
        fi
        
        rm -f "$TEST_STRATEGY"
    else
        echo "⏭️ SKIPPING VALIDATION: No significant improvements found"
    fi
else
    echo "❌ No results file found"
fi

# ===== FINAL SUMMARY =====
echo ""
echo "📄 OPTIMIZATION SUMMARY"
echo "======================"
echo ""
echo "📁 Results saved to: ${RESULTS_DIR}/"
echo "📊 Baseline: ${baseline_usdt} USDT (${baseline_trades} trades)"

if [[ -n "$best_test" ]] && (( $(echo "$best_profit > 0.5" | bc -l 2>/dev/null) )); then
    echo "🏆 Best improvement: $best_test (+${best_profit} USDT)"
    echo ""
    echo "🎯 RECOMMENDED NEXT STEPS:"
    echo "1. ✅ Apply best parameters to production strategy"
    echo "2. 🧪 Run full 6-month backtest for final validation"
    echo "3. 📊 Monitor performance in paper trading"
    echo "4. 🚀 Deploy if consistently better than baseline"
else
    echo "📈 Result: No significant improvements found"
    echo ""
    echo "🎯 ANALYSIS:"
    echo "1. ✅ Current strategy appears well-optimized"
    echo "2. 📊 Consider testing wider parameter ranges"
    echo "3. 🔍 Analyze market conditions for strategy effectiveness"
    echo "4. 🎲 Baseline performance (+8.745 USDT) is solid"
fi

echo ""
echo "🏁 Parameter optimization complete!"

exit 0 