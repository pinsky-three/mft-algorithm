#!/bin/bash

# PHASE 1 OPTIMIZATION TESTING SUITE
# Comprehensive evaluation of advanced scalping optimizations

echo "🚀 PHASE 1 OPTIMIZATION TESTING SUITE"
echo "====================================="
echo "Testing CryptoScalpingAdvanced v1.0 against CryptoScalpingOptimized baseline"
echo "Timeframe: 6 months (Jan-July 2025)"
echo "Pairs: BTC/USDT, ETH/USDT, SOL/USDT"
echo ""

# Create results directory
mkdir -p backtest_results/phase1_testing

# Test periods for comprehensive evaluation
echo "📅 Test Periods:"
echo "1. Full Period: Jan 1 - July 10, 2025 (181 days)"
echo "2. Monthly breakdown for detailed analysis"
echo "3. Volatile periods for stress testing"
echo ""

# Results files
baseline_results="backtest_results/phase1_testing/baseline_results.txt"
advanced_results="backtest_results/phase1_testing/advanced_results.txt"
comparison_results="backtest_results/phase1_testing/comparison_summary.txt"

# Initialize results files
echo "🎯 BASELINE STRATEGY RESULTS (CryptoScalpingOptimized)" > "$baseline_results"
echo "=======================================================" >> "$baseline_results"
echo "Generated: $(date)" >> "$baseline_results"
echo "" >> "$baseline_results"

echo "🚀 ADVANCED STRATEGY RESULTS (CryptoScalpingAdvanced v1.0)" > "$advanced_results"
echo "=========================================================" >> "$advanced_results"  
echo "Generated: $(date)" >> "$advanced_results"
echo "" >> "$advanced_results"

echo "⚖️ STRATEGY COMPARISON ANALYSIS" > "$comparison_results"
echo "===============================" >> "$comparison_results"
echo "Generated: $(date)" >> "$comparison_results"
echo "" >> "$comparison_results"

# Function to extract key metrics from backtest output
extract_metrics() {
    local output="$1"
    local strategy_name="$2"
    
    # Extract core metrics with improved patterns
    local profit_percent=$(echo "$output" | grep "│ Total profit %" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)%[[:space:]]*│.*/\1/')
    local profit_usdt=$(echo "$output" | grep "│ Absolute profit" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)[[:space:]]*USDT[[:space:]]*│.*/\1/')
    local total_trades=$(echo "$output" | grep "│ Total/Daily Avg Trades" | head -1 | sed 's/.*│[[:space:]]*\([0-9]*\)[[:space:]]*\/.*│.*/\1/')
    local win_rate=$(echo "$output" | grep "│    TOTAL │" | head -1 | sed 's/.*│[[:space:]]*[0-9]*[[:space:]]*[0-9]*[[:space:]]*[0-9]*[[:space:]]*\([0-9.]*\)[[:space:]]*│.*/\1/')
    local max_drawdown=$(echo "$output" | grep "│ Max % of account underwater" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)%[[:space:]]*│.*/\1/')
    
    # Extract exit reason statistics
    local roi_exits=$(echo "$output" | grep "│[[:space:]]*roi[[:space:]]*│" | head -1 | awk -F'│' '{print $3}' | awk '{print $1}' | tr -d '\n\r')
    local stop_losses=$(echo "$output" | grep "│[[:space:]]*stop_loss[[:space:]]*│" | head -1 | awk -F'│' '{print $3}' | awk '{print $1}' | tr -d '\n\r')
    
    # Advanced exit reasons for the new strategy
    local roi_base=$(echo "$output" | grep "│[[:space:]]*roi_base_target[[:space:]]*│" | head -1 | awk -F'│' '{print $3}' | awk '{print $1}' | tr -d '\n\r')
    local roi_extended=$(echo "$output" | grep "│[[:space:]]*roi_extended_target[[:space:]]*│" | head -1 | awk -F'│' '{print $3}' | awk '{print $1}' | tr -d '\n\r')
    local trailing_stops=$(echo "$output" | grep "│[[:space:]]*trailing_stop_loss[[:space:]]*│" | head -1 | awk -F'│' '{print $3}' | awk '{print $1}' | tr -d '\n\r')
    local momentum_exits=$(echo "$output" | grep "│[[:space:]]*momentum_exit[[:space:]]*│" | head -1 | awk -F'│' '{print $3}' | awk '{print $1}' | tr -d '\n\r')
    
    # Clean and default values
    profit_percent=${profit_percent:-"0.00"}
    profit_usdt=${profit_usdt:-"0.000"}
    total_trades=${total_trades:-"0"}
    win_rate=${win_rate:-"0.0"}
    max_drawdown=${max_drawdown:-"0.00"}
    roi_exits=${roi_exits:-"0"}
    stop_losses=${stop_losses:-"0"}
    roi_base=${roi_base:-"0"}
    roi_extended=${roi_extended:-"0"}
    trailing_stops=${trailing_stops:-"0"}
    momentum_exits=${momentum_exits:-"0"}
    
    # Output formatted results
    echo "Strategy: $strategy_name"
    echo "Total Profit: ${profit_percent}% (${profit_usdt} USDT)"
    echo "Total Trades: ${total_trades}"
    echo "Win Rate: ${win_rate}%"
    echo "Max Drawdown: ${max_drawdown}%"
    echo "ROI Exits: ${roi_exits}"
    echo "Stop Losses: ${stop_losses}"
    
    if [[ "$strategy_name" == "CryptoScalpingAdvanced" ]]; then
        echo "📊 ADVANCED EXIT BREAKDOWN:"
        echo "  ROI Base Target: ${roi_base}"
        echo "  ROI Extended Target: ${roi_extended}" 
        echo "  Trailing Stops: ${trailing_stops}"
        echo "  Momentum Exits: ${momentum_exits}"
        
        # Calculate advanced exit efficiency
        local total_roi_exits=$((roi_base + roi_extended + roi_exits))
        local exit_efficiency="N/A"
        if [[ $total_trades -gt 0 ]]; then
            exit_efficiency=$(echo "scale=1; ($total_roi_exits * 100) / $total_trades" | bc -l 2>/dev/null || echo "N/A")
        fi
        echo "  Exit Efficiency: ${exit_efficiency}%"
    fi
    echo ""
}

# Test 1: Full 6-Month Period Comparison
echo "🔄 Test 1: Full Period Analysis (Jan 1 - July 10, 2025)"
echo "========================================================="

echo "Testing baseline strategy..."
baseline_output=$(docker compose run --rm freqtrade backtesting -s CryptoScalpingOptimized -p BTC/USDT ETH/USDT SOL/USDT --timerange 20250101-20250710 --fee 0.0002 --timeframe 1m 2>/dev/null | tr -d '\r')

echo "Testing advanced strategy..."
advanced_output=$(docker compose run --rm freqtrade backtesting -s CryptoScalpingAdvanced -p BTC/USDT ETH/USDT SOL/USDT --timerange 20250101-20250710 --fee 0.0002 --timeframe 1m 2>/dev/null | tr -d '\r')

# Extract and save baseline metrics
echo "📊 FULL PERIOD RESULTS - BASELINE" >> "$baseline_results"
echo "=================================" >> "$baseline_results"
baseline_metrics=$(extract_metrics "$baseline_output" "CryptoScalpingOptimized")
echo "$baseline_metrics" >> "$baseline_results"

# Extract and save advanced metrics  
echo "📊 FULL PERIOD RESULTS - ADVANCED" >> "$advanced_results"
echo "==================================" >> "$advanced_results"
advanced_metrics=$(extract_metrics "$advanced_output" "CryptoScalpingAdvanced")
echo "$advanced_metrics" >> "$advanced_results"

echo "✅ Full period testing complete"

# Test 2: Monthly Breakdown Analysis
echo ""
echo "🔄 Test 2: Monthly Performance Analysis"
echo "======================================="

months=(
    "20250101-20250201:January_2025"
    "20250201-20250301:February_2025"  
    "20250301-20250401:March_2025"
    "20250401-20250501:April_2025"
    "20250501-20250601:May_2025"
    "20250601-20250701:June_2025"
    "20250701-20250710:July_2025_partial"
)

echo "📊 MONTHLY BREAKDOWN - BASELINE" >> "$baseline_results"
echo "===============================" >> "$baseline_results"

echo "📊 MONTHLY BREAKDOWN - ADVANCED" >> "$advanced_results"
echo "===============================" >> "$advanced_results"

for month_data in "${months[@]}"; do
    IFS=':' read -r timerange month_name <<< "$month_data"
    
    echo "Testing $month_name..."
    
    # Test baseline
    baseline_month_output=$(docker compose run --rm freqtrade backtesting -s CryptoScalpingOptimized -p BTC/USDT ETH/USDT SOL/USDT --timerange "$timerange" --fee 0.0002 --timeframe 1m 2>/dev/null | tr -d '\r')
    
    # Test advanced
    advanced_month_output=$(docker compose run --rm freqtrade backtesting -s CryptoScalpingAdvanced -p BTC/USDT ETH/USDT SOL/USDT --timerange "$timerange" --fee 0.0002 --timeframe 1m 2>/dev/null | tr -d '\r')
    
    # Save monthly results
    echo "📅 $month_name ($timerange)" >> "$baseline_results"
    baseline_month_metrics=$(extract_metrics "$baseline_month_output" "CryptoScalpingOptimized")
    echo "$baseline_month_metrics" >> "$baseline_results"
    
    echo "📅 $month_name ($timerange)" >> "$advanced_results"
    advanced_month_metrics=$(extract_metrics "$advanced_month_output" "CryptoScalpingAdvanced")  
    echo "$advanced_month_metrics" >> "$advanced_results"
    
    echo "✅ $month_name testing complete"
done

# Test 3: High Volatility Stress Testing
echo ""
echo "🔄 Test 3: High Volatility Stress Testing"
echo "=========================================="

stress_periods=(
    "20250315-20250325:March_Volatility"
    "20250510-20250520:May_Turbulence"
    "20250620-20250630:June_Correction"
)

echo "📊 STRESS TEST RESULTS - BASELINE" >> "$baseline_results"
echo "=================================" >> "$baseline_results"

echo "📊 STRESS TEST RESULTS - ADVANCED" >> "$advanced_results"
echo "==================================" >> "$advanced_results"

for stress_data in "${stress_periods[@]}"; do
    IFS=':' read -r timerange period_name <<< "$stress_data"
    
    echo "Stress testing $period_name..."
    
    # Test baseline under stress
    baseline_stress_output=$(docker compose run --rm freqtrade backtesting -s CryptoScalpingOptimized -p BTC/USDT ETH/USDT SOL/USDT --timerange "$timerange" --fee 0.0002 --timeframe 1m 2>/dev/null | tr -d '\r')
    
    # Test advanced under stress
    advanced_stress_output=$(docker compose run --rm freqtrade backtesting -s CryptoScalpingAdvanced -p BTC/USDT ETH/USDT SOL/USDT --timerange "$timerange" --fee 0.0002 --timeframe 1m 2>/dev/null | tr -d '\r')
    
    # Save stress test results
    echo "⚡ $period_name ($timerange)" >> "$baseline_results"
    baseline_stress_metrics=$(extract_metrics "$baseline_stress_output" "CryptoScalpingOptimized")
    echo "$baseline_stress_metrics" >> "$baseline_results"
    
    echo "⚡ $period_name ($timerange)" >> "$advanced_results"
    advanced_stress_metrics=$(extract_metrics "$advanced_stress_output" "CryptoScalpingAdvanced")
    echo "$advanced_stress_metrics" >> "$advanced_results"
    
    echo "✅ $period_name stress testing complete"
done

# Generate Comparison Summary
echo ""
echo "📊 Generating Comparison Analysis..."

# Extract key metrics for comparison (you would parse the results files here)
echo "⚖️ STRATEGY COMPARISON SUMMARY" >> "$comparison_results"
echo "=============================" >> "$comparison_results"
echo "" >> "$comparison_results"
echo "🎯 PHASE 1 OPTIMIZATION TARGETS:" >> "$comparison_results"
echo "Conservative: 2.5-3.5% profit, 70-75% win rate" >> "$comparison_results"
echo "Aggressive: 4.5-6.0% profit, 75-80% win rate" >> "$comparison_results"
echo "" >> "$comparison_results"
echo "📈 EXPECTED IMPROVEMENTS:" >> "$comparison_results"
echo "- Advanced Exits: +30-50% profit capture" >> "$comparison_results"
echo "- Position Sizing: +25-40% profit optimization" >> "$comparison_results"
echo "- Multi-timeframe: +15-25% win rate" >> "$comparison_results"
echo "- ML Regimes: +20-30% profit" >> "$comparison_results"
echo "- Ensemble: +20-35% reliability" >> "$comparison_results"
echo "" >> "$comparison_results"
echo "📊 DETAILED RESULTS:" >> "$comparison_results"
echo "See baseline_results.txt and advanced_results.txt for full metrics" >> "$comparison_results"
echo "" >> "$comparison_results"

# Final summary
echo ""
echo "✅ PHASE 1 OPTIMIZATION TESTING COMPLETE!"
echo "=========================================="
echo ""
echo "📄 Results saved to:"
echo "  - Baseline: $baseline_results"
echo "  - Advanced: $advanced_results"  
echo "  - Comparison: $comparison_results"
echo ""
echo "🎯 Review the results to validate Phase 1 improvements:"
echo "  1. Profit improvement from advanced exits"
echo "  2. Win rate enhancement from multi-timeframe confluence"
echo "  3. Risk reduction from adaptive position sizing"
echo "  4. Market regime adaptation effectiveness"
echo "  5. Overall strategy robustness under stress"
echo ""
echo "🚀 If results meet targets, proceed to Phase 2 optimizations!" 