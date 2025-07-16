#!/bin/bash

# 🎯 SIMPLE PARAMETER OPTIMIZATION
# =================================
# Manual testing of key parameters one at a time

echo "🚀 SIMPLE PARAMETER OPTIMIZATION"
echo "================================"
echo ""

TIMERANGE="20250101-20250501"  # 4 months training
PAIRS="BTC/USDT ETH/USDT SOL/USDT"
ORIGINAL_STRATEGY="user_data/strategies/CryptoScalpingOptimized.py"

echo "📊 Testing period: ${TIMERANGE}"
echo "💰 Pairs: ${PAIRS}"
echo ""

# ===== BASELINE TEST =====
echo "🔍 BASELINE TEST"
echo "================"

baseline_output=$(docker compose run --rm freqtrade backtesting \
    -s CryptoScalpingOptimized \
    -p ${PAIRS} \
    --timerange ${TIMERANGE} \
    --fee 0.0002 \
    --timeframe 1m \
    2>/dev/null)

baseline_profit=$(echo "$baseline_output" | grep "│ Total profit %" | head -1 | awk -F'│' '{print $3}' | tr -d ' %')
baseline_usdt=$(echo "$baseline_output" | grep "│ Absolute profit" | head -1 | awk -F'│' '{print $3}' | tr -d ' USDT')
baseline_trades=$(echo "$baseline_output" | grep "│ Total/Daily Avg Trades" | head -1 | awk -F'│' '{print $3}' | awk '{print $1}')

echo "✅ BASELINE: ${baseline_profit}% (${baseline_usdt} USDT), ${baseline_trades} trades"
echo ""

# ===== TEST FUNCTION =====
test_modification() {
    local test_name="$1"
    local description="$2"
    local search_pattern="$3"
    local replacement="$4"
    
    echo "🔄 Testing: ${test_name}"
    echo "   ${description}"
    
    # Create test strategy
    cp "$ORIGINAL_STRATEGY" "user_data/strategies/TestStrategy.py"
    
    # Rename class
    sed -i.bak 's/class CryptoScalpingOptimized/class TestStrategy/' "user_data/strategies/TestStrategy.py"
    
    # Apply modification
    sed -i.bak "s/${search_pattern}/${replacement}/" "user_data/strategies/TestStrategy.py"
    
    # Clean backup
    rm -f "user_data/strategies/TestStrategy.py.bak"
    
    # Run test
    test_output=$(docker compose run --rm freqtrade backtesting \
        -s TestStrategy \
        -p ${PAIRS} \
        --timerange ${TIMERANGE} \
        --fee 0.0002 \
        --timeframe 1m \
        2>/dev/null)
    
    # Extract results
    test_profit=$(echo "$test_output" | grep "│ Total profit %" | head -1 | awk -F'│' '{print $3}' | tr -d ' %')
    test_usdt=$(echo "$test_output" | grep "│ Absolute profit" | head -1 | awk -F'│' '{print $3}' | tr -d ' USDT')
    test_trades=$(echo "$test_output" | grep "│ Total/Daily Avg Trades" | head -1 | awk -F'│' '{print $3}' | awk '{print $1}')
    
    # Calculate difference
    if [[ -n "$test_usdt" && -n "$baseline_usdt" ]]; then
        profit_diff=$(echo "scale=3; $test_usdt - $baseline_usdt" | bc -l 2>/dev/null || echo "0")
    else
        profit_diff="0"
    fi
    
    # Status
    if (( $(echo "$profit_diff > 1.0" | bc -l 2>/dev/null) )); then
        status="✅ IMPROVEMENT"
    elif (( $(echo "$profit_diff > 0.2" | bc -l 2>/dev/null) )); then
        status="🟡 MARGINAL"
    elif (( $(echo "$profit_diff < -1.0" | bc -l 2>/dev/null) )); then
        status="❌ LOSS"
    else
        status="⚪ NEUTRAL"
    fi
    
    echo "   Result: ${test_profit}% (${test_usdt} USDT), ${test_trades} trades"
    echo "   vs Baseline: ${status} (${profit_diff:+}${profit_diff} USDT)"
    echo ""
    
    # Save to results
    echo "${test_name}|${profit_diff}|${test_usdt}|${test_trades}|${status}" >> "simple_optimization_results.txt"
    
    # Clean up
    rm -f "user_data/strategies/TestStrategy.py"
}

# ===== RUN TESTS =====
echo "🧪 RUNNING PARAMETER TESTS"
echo "=========================="
echo ""

# Initialize results
echo "# Simple Optimization Results" > "simple_optimization_results.txt"
echo "test_name|profit_diff|usdt|trades|status" >> "simple_optimization_results.txt"

# Test 1: ROI Aggressive (Higher targets)
test_modification "roi_aggressive" "Higher ROI targets: 3.0%/2.5%/2.0%" \
    '"0": 0.025' '"0": 0.030'

# Test 2: ROI Conservative (Lower targets)  
test_modification "roi_conservative" "Lower ROI targets: 2.0%/1.5%/1.0%" \
    '"0": 0.025' '"0": 0.020'

# Test 3: Tighter Stop Loss
test_modification "risk_tight" "Tighter stop loss: -2.0%" \
    'stoploss: float = -0.025' 'stoploss: float = -0.020'

# Test 4: Looser Stop Loss
test_modification "risk_loose" "Looser stop loss: -3.0%" \
    'stoploss: float = -0.025' 'stoploss: float = -0.030'

# Test 5: Relaxed Market Health
test_modification "health_relaxed" "Relaxed market health: 0.4 (was 0.5)" \
    'MIN_MARKET_HEALTH = 0.5' 'MIN_MARKET_HEALTH = 0.4'

# Test 6: Strict Market Health
test_modification "health_strict" "Strict market health: 0.6 (was 0.5)" \
    'MIN_MARKET_HEALTH = 0.5' 'MIN_MARKET_HEALTH = 0.6'

# Test 7: Lower Volume Requirement
test_modification "volume_relaxed" "Lower volume requirement: 1.7x (was 1.9x)" \
    'MIN_VOLUME_RATIO = 1.9' 'MIN_VOLUME_RATIO = 1.7'

# Test 8: Higher Volume Requirement
test_modification "volume_strict" "Higher volume requirement: 2.1x (was 1.9x)" \
    'MIN_VOLUME_RATIO = 1.9' 'MIN_VOLUME_RATIO = 2.1'

# ===== ANALYZE RESULTS =====
echo "📊 RESULTS SUMMARY"
echo "=================="
echo ""

if [[ -f "simple_optimization_results.txt" ]]; then
    # Sort by profit difference
    tail -n +3 "simple_optimization_results.txt" | sort -t'|' -k2 -nr > "sorted_results.txt"
    
    echo "🏆 RANKED RESULTS:"
    echo "=================="
    rank=1
    while IFS='|' read -r test_name profit_diff usdt trades status; do
        printf "%2d. %-18s %s (%+.3f USDT) - %s USDT, %s trades\n" \
            "$rank" "$test_name" "$status" "$profit_diff" "$usdt" "$trades"
        rank=$((rank + 1))
    done < "sorted_results.txt"
    
    echo ""
    
    # Best result
    best_line=$(head -1 "sorted_results.txt")
    IFS='|' read -r best_test best_profit best_usdt best_trades best_status <<< "$best_line"
    
    if (( $(echo "$best_profit > 0.5" | bc -l 2>/dev/null) )); then
        echo "🎉 BEST RESULT: $best_test"
        echo "   Improvement: +${best_profit} USDT"
        echo "   Total: ${best_usdt} USDT with ${best_trades} trades"
        echo ""
        echo "🎯 RECOMMENDATION: Test this parameter on validation data"
    else
        echo "📈 CONCLUSION: No significant improvements found"
        echo "   Current strategy appears well-optimized"
        echo "   Baseline ${baseline_usdt} USDT performance is solid"
    fi
    
else
    echo "❌ No results file found"
fi

echo ""
echo "📁 Results saved to: simple_optimization_results.txt"
echo "🏁 Simple optimization complete!"

exit 0 