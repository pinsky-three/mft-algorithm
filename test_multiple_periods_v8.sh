#!/bin/bash

# Cross-Validation Testing for MultiHorizonMomentum Strategy v8 - TEMA Extended
# Testing multiple periods to validate strategy consistency

echo "=================================================================="
echo "Cross-Validation Testing - MultiHorizonMomentum Strategy v8"
echo "=================================================================="
echo "Testing across multiple market conditions and periods..."
echo ""

# Test parameters
STRATEGY="MultiHorizonMomentum"
PAIRS="BTC/USDT"
TIMEFRAME="1m"
FEE="0.0002"  # 0.02% realistic fees

# Define multiple test periods
declare -a PERIODS=(
    "20240701-20240731:Jul-2024"
    "20240801-20240831:Aug-2024" 
    "20240901-20240930:Sep-2024"
    "20241001-20241031:Oct-2024"
    "20241101-20241130:Nov-2024"
    "20241201-20241210:Dec-2024"
)

echo "Strategy: $STRATEGY"
echo "Pair: $PAIRS"
echo "Timeframe: $TIMEFRAME"
echo "Fees: $FEE%"
echo "Periods to test: ${#PERIODS[@]}"
echo ""

# Create results directory
mkdir -p user_data/backtest_results/cross_validation_v8

# Function to run backtest for a specific period
run_period_test() {
    local period_range=$1
    local period_name=$2
    
    echo ">>> Testing period: $period_name ($period_range)"
    
    # With fees
    docker compose run --rm freqtrade backtesting \
        --strategy $STRATEGY \
        --pairs $PAIRS \
        --timeframe $TIMEFRAME \
        --fee $FEE \
        --timerange $period_range \
        --export trades \
        --export-filename user_data/backtest_results/cross_validation_v8/${period_name}_with_fees.json \
        --cache=none > /tmp/backtest_${period_name}_fees.log 2>&1
    
    # Extract key metrics from log
    local trades=$(grep "Total/Daily Avg Trades" /tmp/backtest_${period_name}_fees.log | awk '{print $5}' | sed 's/\///g')
    local win_rate=$(grep -E "│\s+TOTAL\s+│" /tmp/backtest_${period_name}_fees.log | tail -1 | awk '{print $NF}')
    local profit=$(grep "Total profit %" /tmp/backtest_${period_name}_fees.log | awk '{print $5}' | sed 's/%//g')
    local drawdown=$(grep "Max % of account underwater" /tmp/backtest_${period_name}_fees.log | awk '{print $8}' | sed 's/%//g')
    
    echo "   Trades: ${trades:-N/A} | Win Rate: ${win_rate:-N/A} | Profit: ${profit:-N/A}% | Drawdown: ${drawdown:-N/A}%"
    
    # Without fees (quick validation)
    docker compose run --rm freqtrade backtesting \
        --strategy $STRATEGY \
        --pairs $PAIRS \
        --timeframe $TIMEFRAME \
        --fee 0 \
        --timerange $period_range \
        --export trades \
        --export-filename user_data/backtest_results/cross_validation_v8/${period_name}_no_fees.json \
        --cache=none > /tmp/backtest_${period_name}_no_fees.log 2>&1
    
    local win_rate_no_fees=$(grep -E "│\s+TOTAL\s+│" /tmp/backtest_${period_name}_no_fees.log | tail -1 | awk '{print $NF}')
    local profit_no_fees=$(grep "Total profit %" /tmp/backtest_${period_name}_no_fees.log | awk '{print $5}' | sed 's/%//g')
    
    echo "   No Fees - Win Rate: ${win_rate_no_fees:-N/A} | Profit: ${profit_no_fees:-N/A}%"
    echo ""
}

# Run tests for each period
for period in "${PERIODS[@]}"; do
    IFS=':' read -r period_range period_name <<< "$period"
    run_period_test "$period_range" "$period_name"
done

# Full period test for comparison
echo ">>> Testing full period: Jul-Dec 2024"
docker compose run --rm freqtrade backtesting \
    --strategy $STRATEGY \
    --pairs $PAIRS \
    --timeframe $TIMEFRAME \
    --fee $FEE \
    --timerange 20240701-20241210 \
    --export trades \
    --export-filename user_data/backtest_results/cross_validation_v8/full_period_with_fees.json \
    --cache=none > /tmp/backtest_full_period.log 2>&1

echo ""
echo "=================================================================="
echo "Cross-Validation Summary:"
echo "=================================================================="
echo "✓ Tested 6 monthly periods + full period"
echo "✓ Both with fees (0.02%) and without fees" 
echo "✓ Results saved to user_data/backtest_results/cross_validation_v8/"
echo ""
echo "Key Analysis Points:"
echo "📊 Consistency: Check if win rates are similar across periods"
echo "📈 Market Conditions: Different periods = different market phases"
echo "⚡ Robustness: Strategy should work in various conditions"
echo "🎯 Fee Impact: Compare with/without fees for edge validation"
echo ""
echo "Next Steps:"
echo "1. Review individual period performance"
echo "2. Identify best/worst performing periods"
echo "3. Analyze market conditions during poor performance"
echo "4. Decide on optimizations based on cross-validation results"
echo ""
echo "To view detailed results:"
echo "ls -la user_data/backtest_results/cross_validation_v8/" 