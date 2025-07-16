#!/bin/bash

# Hyperparameter Optimization Script
# ==================================
# Conservative optimization approach to improve existing successful strategy
# Based on memory: "Phase 3 Final with smart regime detection performed WORSE"

echo "🚀 HYPERPARAMETER OPTIMIZATION - CONSERVATIVE APPROACH"
echo "======================================================"
echo ""
echo "🎯 GOAL: Improve +8.745 USDT baseline without over-engineering"
echo "⚠️  APPROACH: Conservative ranges, risk-adjusted optimization"
echo "📊 BASELINE: 254 trades, 1.457 USDT avg monthly, +8.745 USDT total"
echo ""

# ===== OPTIMIZATION CONFIGURATION =====

# Training period (4 profitable months)
TRAIN_TIMERANGE="20250101-20250501"

# Validation period (1 month out-of-sample)
VALIDATION_TIMERANGE="20250501-20250601"

# Test pairs
PAIRS="BTC/USDT ETH/USDT SOL/USDT"

# Optimization settings
EPOCHS=100                           # Conservative epoch count
HYPEROPT_LOSS="SortinoHyperOptLoss"   # Use Sortino, more robust to skewed returns
TIMEFRAME="1m"
FEE="0.0002"

# Results directory
RESULTS_DIR="hyperopt_results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

echo "📅 Training Period: ${TRAIN_TIMERANGE}"
echo "📅 Validation Period: ${VALIDATION_TIMERANGE}"
echo "💰 Pairs: ${PAIRS}"
echo "🔧 Epochs: ${EPOCHS}"
echo "📊 Loss Function: ${HYPEROPT_LOSS}"
echo "📁 Results Directory: ${RESULTS_DIR}"
echo ""

# ===== PREREQUISITE CHECK =====

echo "🔍 PREREQUISITE CHECK"
echo "===================="

# Check if baseline verification passed
if [ ! -f "baseline_comparison.txt" ]; then
    echo "❌ ERROR: Baseline verification not found!"
    echo "   Run ./test_hyperopt_baseline.sh first"
    exit 1
fi

# Check if baseline passed
baseline_status=$(grep "Baseline Match:" baseline_comparison.txt | grep -o "✅\|❌")
if [ "$baseline_status" != "✅" ]; then
    echo "❌ ERROR: Baseline verification failed!"
    echo "   The hyperopt strategy must match the original exactly before optimization"
    echo "   Fix the hyperopt strategy implementation first"
    echo ""
    echo "📄 See baseline_comparison.txt for details"
    exit 1
fi

echo "✅ Baseline verification passed - safe to optimize"
echo ""

# ===== OPTIMIZATION SPACES =====

echo "🎛️  OPTIMIZATION CONFIGURATION"
echo "=============================="
echo ""

# Define optimization spaces to run
spaces=(
    "buy"                    # Market health and entry parameters
    "roi"                    # ROI ladder optimization  
    "stoploss"              # Risk management
    "buy roi"               # Combined entry + ROI
    "buy roi stoploss"      # Full optimization
)

space_descriptions=(
    "Market Health & Entry Quality (Conservative)"
    "ROI Ladder Optimization (Risk/Reward)"
    "Stoploss Risk Management" 
    "Combined Entry + ROI"
    "Full Parameter Optimization"
)

echo "📊 Optimization Spaces:"
for i in "${!spaces[@]}"; do
    printf "   %d. %-20s - %s\n" $((i+1)) "${spaces[$i]}" "${space_descriptions[$i]}"
done
echo ""

# ===== RUN OPTIMIZATIONS =====

echo "🚀 STARTING HYPERPARAMETER OPTIMIZATION"
echo "======================================="
echo ""

best_result=""
best_profit=0
best_space=""

for i in "${!spaces[@]}"; do
    space="${spaces[$i]}"
    description="${space_descriptions[$i]}"
    
    echo "🔄 Optimizing Space $((i+1))/5: ${space}"
    echo "   Description: ${description}"
    echo "   Started: $(date)"
    echo ""
    
    # Create space-specific results file
    space_file="${RESULTS_DIR}/hyperopt_${space// /_}_results.txt"
    
    # Run hyperopt optimization
    echo "🎯 Running optimization..."
    optimization_output=$(docker compose run --rm freqtrade hyperopt \
        --strategy CryptoScalpingOptimizedHyperopt \
        --hyperopt CryptoScalpingOptimizedHyperOpt \
        --hyperopt-loss ${HYPEROPT_LOSS} \
        --epochs ${EPOCHS} \
        --timerange ${TRAIN_TIMERANGE} \
        --timeframe ${TIMEFRAME} \
        --fee ${FEE} \
        --spaces ${space} \
        -p ${PAIRS} \
        2>/dev/null)
    
    # Save optimization output
    echo "$optimization_output" > "$space_file"
    
    # Extract best result
    best_params=$(echo "$optimization_output" | grep -A 20 "Best result:" | head -20)
    best_sharpe=$(echo "$optimization_output" | grep "Best result:" | sed 's/.*Sharpe: \([0-9.-]*\).*/\1/')
    
    echo "✅ Optimization Complete"
    echo "   Best Sharpe: ${best_sharpe:-'N/A'}"
    echo "   Results saved: ${space_file}"
    echo ""
    
    # Track best overall result
    if [ -n "$best_sharpe" ] && (( $(echo "$best_sharpe > $best_profit" | bc -l) )); then
        best_profit="$best_sharpe"
        best_space="$space"
        best_result="$best_params"
    fi
    
    echo "⏱️  Completed: $(date)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
done

# ===== BEST RESULT SUMMARY =====

echo "🏆 OPTIMIZATION SUMMARY"
echo "======================"
echo ""

if [ -n "$best_result" ]; then
    echo "🥇 Best Overall Result:"
    echo "   Space: ${best_space}"
    echo "   Sharpe Ratio: ${best_profit}"
    echo ""
    echo "📊 Best Parameters:"
    echo "$best_result"
    echo ""
    
    # Save best result
    best_result_file="${RESULTS_DIR}/BEST_RESULT.txt"
    echo "🏆 BEST HYPEROPT RESULT" > "$best_result_file"
    echo "======================" >> "$best_result_file"
    echo "Space: ${best_space}" >> "$best_result_file"
    echo "Sharpe Ratio: ${best_profit}" >> "$best_result_file"
    echo "Optimization Date: $(date)" >> "$best_result_file"
    echo "" >> "$best_result_file"
    echo "Best Parameters:" >> "$best_result_file"
    echo "$best_result" >> "$best_result_file"
    
else
    echo "❌ No valid optimization results found"
    echo "   Check individual space results in ${RESULTS_DIR}/"
fi

echo ""

# ===== VALIDATION =====

echo "🧪 OUT-OF-SAMPLE VALIDATION"
echo "==========================="
echo ""

if [ -n "$best_result" ]; then
    echo "🔄 Running validation on ${VALIDATION_TIMERANGE}..."
    echo "   This tests the optimized parameters on unseen data"
    echo ""
    
    # Extract optimized parameters (this would need to be implemented based on freqtrade hyperopt output format)
    echo "⚠️  Manual step required:"
    echo "   1. Apply best parameters to CryptoScalpingOptimizedHyperopt.py"
    echo "   2. Run validation backtest:"
    echo "      docker compose run --rm freqtrade backtesting \\"
    echo "        -s CryptoScalpingOptimizedHyperopt \\"
    echo "        -p ${PAIRS} \\"
    echo "        --timerange ${VALIDATION_TIMERANGE} \\"
    echo "        --fee ${FEE} \\"
    echo "        --timeframe ${TIMEFRAME}"
    echo ""
    echo "   3. Compare validation results to baseline June 2025 performance"
    echo "      Baseline June: 0.04% (0.402 USDT), 14 trades, 64.3% win rate"
    echo ""
else
    echo "❌ Skipping validation - no optimization results to validate"
fi

# ===== FINAL REPORT =====

echo "📄 FINAL REPORT"
echo "==============="
echo ""
echo "📁 Results Directory: ${RESULTS_DIR}/"
echo "📊 Files Generated:"
ls -la "$RESULTS_DIR/"
echo ""

echo "🎯 NEXT STEPS:"
echo "1. Review optimization results in ${RESULTS_DIR}/"
echo "2. Apply best parameters to strategy (manual step)"
echo "3. Run out-of-sample validation"
echo "4. Compare to baseline monthly performance"
echo "5. Deploy if better than baseline (+8.745 USDT)"
echo ""

echo "⚠️  VALIDATION CRITERIA:"
echo "- Must beat baseline: +8.745 USDT over 6 months"
echo "- Must maintain monthly consistency (no negative months)"
echo "- Must not reduce trade count below 150 (current: 254)"
echo "- Must improve risk-adjusted returns (Sharpe ratio)"
echo ""

echo "🏁 Hyperparameter optimization complete!"
echo "   Remember: Only deploy if better than proven baseline [[memory:3232431]]"

exit 0 