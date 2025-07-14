#!/bin/bash

echo "🚀 PHASE 3 COMPREHENSIVE TESTING - CONSISTENCY & PROFIT VALIDATION"
echo "=================================================================="
echo "Testing Period: January 2025 - June 2025 (6 months)"
echo "Strategies: Baseline → Phase 1 → Phase 2 → Phase 3"
echo "Focus: Eliminate negative months, improve consistency"
echo ""

# Test periods for monthly analysis
months=(
    "20250101-20250201"  # January 2025
    "20250201-20250301"  # February 2025  
    "20250301-20250401"  # March 2025
    "20250401-20250501"  # April 2025
    "20250501-20250601"  # May 2025
    "20250601-20250701"  # June 2025
)

month_names=(
    "January_2025"
    "February_2025"
    "March_2025" 
    "April_2025"
    "May_2025"
    "June_2025"
)

strategies=(
    "CryptoScalpingOptimized"
    "CryptoScalpingAdvanced"
    "CryptoScalpingPhase2"
    "CryptoScalpingPhase3"
)

strategy_labels=(
    "BASELINE"
    "PHASE_1"
    "PHASE_2"
    "PHASE_3"
)

# Output file
results_file="phase3_comprehensive_results.txt"

echo "🎯 PHASE 3 COMPREHENSIVE BACKTEST ANALYSIS" > "$results_file"
echo "==========================================" >> "$results_file"
echo "Objective: Validate Phase 3 consistency improvements" >> "$results_file"
echo "Period: January 2025 - June 2025 (6 months)" >> "$results_file"
echo "Pairs: BTC/USDT, ETH/USDT, SOL/USDT" >> "$results_file"
echo "Timeframe: 1m" >> "$results_file"
echo "Generated: $(date)" >> "$results_file"
echo "" >> "$results_file"

# Initialize summary arrays
declare -A total_profits
declare -A total_trades
declare -A negative_months
declare -A win_rates

# Initialize totals
for strategy in "${strategy_labels[@]}"; do
    total_profits[$strategy]=0
    total_trades[$strategy]=0
    negative_months[$strategy]=0
done

echo "📊 MONTHLY BREAKDOWN BY STRATEGY" >> "$results_file"
echo "=================================" >> "$results_file"

# Test each strategy across all months
for s in "${!strategies[@]}"; do
    strategy="${strategies[$s]}"
    label="${strategy_labels[$s]}"
    
    echo "" >> "$results_file"
    echo "🔧 STRATEGY: $label ($strategy)" >> "$results_file"
    echo "----------------------------------------" >> "$results_file"
    
    echo "🔄 Testing $label strategy across 6 months..."
    
    monthly_profits=()
    monthly_trades=()
    monthly_winrates=()
    
    for i in "${!months[@]}"; do
        timerange="${months[$i]}"
        month_name="${month_names[$i]}"
        
        echo "   Testing $month_name..."
        
        # Run backtest with error handling
        output=$(timeout 300 docker compose run --rm freqtrade backtesting \
            -s "$strategy" \
            -p BTC/USDT ETH/USDT SOL/USDT \
            --timerange "$timerange" \
            --fee 0.0002 \
            --timeframe 1m 2>/dev/null | tr -d '\r' || echo "TIMEOUT_ERROR")
        
        if [[ "$output" == "TIMEOUT_ERROR" ]] || [[ -z "$output" ]]; then
            echo "   ⚠️  Timeout or error for $month_name, skipping..."
            echo "   $month_name: ERROR (timeout/failed)" >> "$results_file"
            continue
        fi
        
        # Extract metrics with enhanced error handling
        profit_percent=$(echo "$output" | grep "│ Total profit %" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)%[[:space:]]*│.*/\1/' | head -c 10)
        profit_usdt=$(echo "$output" | grep "│ Absolute profit" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)[[:space:]]*USDT[[:space:]]*│.*/\1/' | head -c 10)
        total_trades_month=$(echo "$output" | grep "│ Total/Daily Avg Trades" | head -1 | sed 's/.*│[[:space:]]*\([0-9]*\)[[:space:]]*\/.*│.*/\1/' | head -c 5)
        win_rate=$(echo "$output" | grep "│    TOTAL │" | head -1 | sed 's/.*│[[:space:]]*[0-9]*[[:space:]]*[0-9]*[[:space:]]*[0-9]*[[:space:]]*\([0-9.]*\)[[:space:]]*│.*/\1/' | head -c 10)
        max_drawdown=$(echo "$output" | grep "│ Max % of account underwater" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)%[[:space:]]*│.*/\1/' | head -c 10)
        
        # Clean and validate data
        profit_percent=${profit_percent:-"0.00"}
        profit_usdt=${profit_usdt:-"0.000"}
        total_trades_month=${total_trades_month:-"0"}
        win_rate=${win_rate:-"0.0"}
        max_drawdown=${max_drawdown:-"0.00"}
        
        # Remove non-numeric characters
        profit_percent=$(echo "$profit_percent" | sed 's/[^0-9.-]//g')
        profit_usdt=$(echo "$profit_usdt" | sed 's/[^0-9.-]//g')
        total_trades_month=$(echo "$total_trades_month" | sed 's/[^0-9]//g')
        win_rate=$(echo "$win_rate" | sed 's/[^0-9.]//g')
        max_drawdown=$(echo "$max_drawdown" | sed 's/[^0-9.-]//g')
        
        # Set defaults for empty values
        profit_percent=${profit_percent:-"0.00"}
        profit_usdt=${profit_usdt:-"0.000"}
        total_trades_month=${total_trades_month:-"0"}
        win_rate=${win_rate:-"0.0"}
        max_drawdown=${max_drawdown:-"0.00"}
        
        # Store for summary
        monthly_profits+=("$profit_percent")
        monthly_trades+=("$total_trades_month")
        monthly_winrates+=("$win_rate")
        
        # Track negative months
        if [[ "$profit_percent" =~ ^-.*$ ]] || [[ "$profit_percent" == "0.00" ]]; then
            ((negative_months[$label]++))
        fi
        
        # Add to totals
        if [[ "$profit_usdt" =~ ^-?[0-9]+\.?[0-9]*$ ]]; then
            total_profits[$label]=$(echo "${total_profits[$label]} + $profit_usdt" | bc -l 2>/dev/null || echo "${total_profits[$label]}")
        fi
        if [[ "$total_trades_month" =~ ^[0-9]+$ ]]; then
            total_trades[$label]=$((${total_trades[$label]} + total_trades_month))
        fi
        
        # Write month result
        echo "   $month_name: ${profit_percent}% (${profit_usdt} USDT), ${total_trades_month} trades, ${win_rate}% WR, ${max_drawdown}% DD" >> "$results_file"
        
        echo "   ✅ $month_name: ${profit_percent}% (${total_trades_month} trades, ${win_rate}% WR)"
    done
    
    # Calculate averages for this strategy
    avg_monthly_profit=$(echo "scale=3; ${total_profits[$label]} / 6" | bc -l 2>/dev/null || echo "0.000")
    avg_trades_per_month=$(echo "scale=1; ${total_trades[$label]} / 6" | bc -l 2>/dev/null || echo "0.0")
    
    echo "" >> "$results_file"
    echo "   📊 $label SUMMARY:" >> "$results_file"
    echo "   Total Period Profit: ${total_profits[$label]} USDT" >> "$results_file"
    echo "   Average Monthly: ${avg_monthly_profit} USDT" >> "$results_file"
    echo "   Total Trades: ${total_trades[$label]}" >> "$results_file"
    echo "   Average Trades/Month: ${avg_trades_per_month}" >> "$results_file"
    echo "   Negative Months: ${negative_months[$label]}/6" >> "$results_file"
    echo "" >> "$results_file"
done

# === COMPARATIVE ANALYSIS ===
echo "" >> "$results_file"
echo "🔍 COMPARATIVE ANALYSIS" >> "$results_file"
echo "========================" >> "$results_file"

# Phase comparison
echo "" >> "$results_file"
echo "📈 PROFIT PROGRESSION:" >> "$results_file"
for strategy in "${strategy_labels[@]}"; do
    avg_monthly=$(echo "scale=3; ${total_profits[$strategy]} / 6" | bc -l 2>/dev/null || echo "0.000")
    echo "   $strategy: ${total_profits[$strategy]} USDT (${avg_monthly} USDT/month)" >> "$results_file"
done

echo "" >> "$results_file"
echo "📊 CONSISTENCY METRICS:" >> "$results_file"
for strategy in "${strategy_labels[@]}"; do
    consistency_score=$(echo "scale=1; (6 - ${negative_months[$strategy]}) * 100 / 6" | bc -l 2>/dev/null || echo "0.0")
    echo "   $strategy: ${negative_months[$strategy]}/6 negative months (${consistency_score}% consistency)" >> "$results_file"
done

echo "" >> "$results_file"
echo "🎯 TRADING VOLUME:" >> "$results_file"
for strategy in "${strategy_labels[@]}"; do
    avg_trades=$(echo "scale=1; ${total_trades[$strategy]} / 6" | bc -l 2>/dev/null || echo "0.0")
    echo "   $strategy: ${total_trades[$strategy]} total trades (${avg_trades} trades/month)" >> "$results_file"
done

# === SUCCESS CRITERIA EVALUATION ===
echo "" >> "$results_file"
echo "🏆 PHASE 3 SUCCESS CRITERIA EVALUATION" >> "$results_file"
echo "=======================================" >> "$results_file"

phase3_profit=${total_profits["PHASE_3"]}
phase3_negative=${negative_months["PHASE_3"]}
phase3_trades=${total_trades["PHASE_3"]}
phase3_avg_monthly=$(echo "scale=3; $phase3_profit / 6" | bc -l 2>/dev/null || echo "0.000")
phase3_avg_trades=$(echo "scale=1; $phase3_trades / 6" | bc -l 2>/dev/null || echo "0.0")

echo "PHASE 3 RESULTS vs TARGETS:" >> "$results_file"
echo "" >> "$results_file"

# Target 1: Eliminate negative months
if [[ ${negative_months["PHASE_3"]} -eq 0 ]]; then
    echo "✅ ELIMINATE NEGATIVE MONTHS: 0/6 negative months (TARGET: 0/6)" >> "$results_file"
else
    echo "❌ ELIMINATE NEGATIVE MONTHS: ${negative_months["PHASE_3"]}/6 negative months (TARGET: 0/6)" >> "$results_file"
fi

# Target 2: 1.5%+ monthly profit
target_check=$(echo "$phase3_avg_monthly >= 1.5" | bc -l 2>/dev/null || echo "0")
if [[ "$target_check" -eq 1 ]]; then
    echo "✅ MONTHLY PROFIT: ${phase3_avg_monthly} USDT/month (TARGET: ≥1.5 USDT/month)" >> "$results_file"
else
    echo "❌ MONTHLY PROFIT: ${phase3_avg_monthly} USDT/month (TARGET: ≥1.5 USDT/month)" >> "$results_file"
fi

# Target 3: Max 80 trades/month
trades_check=$(echo "$phase3_avg_trades <= 80" | bc -l 2>/dev/null || echo "1")
if [[ "$trades_check" -eq 1 ]]; then
    echo "✅ TRADE VOLUME: ${phase3_avg_trades} trades/month (TARGET: ≤80 trades/month)" >> "$results_file"
else
    echo "❌ TRADE VOLUME: ${phase3_avg_trades} trades/month (TARGET: ≤80 trades/month)" >> "$results_file"
fi

# === IMPROVEMENT ANALYSIS ===
echo "" >> "$results_file"
echo "📊 IMPROVEMENT ANALYSIS (Phase 3 vs Previous Phases)" >> "$results_file"
echo "====================================================" >> "$results_file"

# vs Phase 2
phase2_profit=${total_profits["PHASE_2"]}
phase2_negative=${negative_months["PHASE_2"]}

profit_improvement=$(echo "scale=1; ($phase3_profit - $phase2_profit) * 100 / ($phase2_profit + 0.001)" | bc -l 2>/dev/null || echo "0.0")
consistency_improvement=$((6 - phase3_negative - (6 - phase2_negative)))

echo "vs PHASE 2:" >> "$results_file"
echo "   Profit Change: ${profit_improvement}%" >> "$results_file"
echo "   Consistency Change: ${consistency_improvement} fewer negative months" >> "$results_file"

# vs Baseline
baseline_profit=${total_profits["BASELINE"]}
baseline_negative=${negative_months["BASELINE"]}

baseline_improvement=$(echo "scale=1; ($phase3_profit - $baseline_profit) * 100 / ($baseline_profit + 0.001)" | bc -l 2>/dev/null || echo "0.0")
baseline_consistency=$((6 - phase3_negative - (6 - baseline_negative)))

echo "" >> "$results_file"
echo "vs BASELINE:" >> "$results_file"
echo "   Profit Change: ${baseline_improvement}%" >> "$results_file"
echo "   Consistency Change: ${baseline_consistency} fewer negative months" >> "$results_file"

# === FINAL ASSESSMENT ===
echo "" >> "$results_file"
echo "🎯 FINAL ASSESSMENT" >> "$results_file"
echo "===================" >> "$results_file"

# Calculate overall success score
success_criteria=0
total_criteria=3

if [[ ${negative_months["PHASE_3"]} -eq 0 ]]; then
    ((success_criteria++))
fi

target_check=$(echo "$phase3_avg_monthly >= 1.5" | bc -l 2>/dev/null || echo "0")
if [[ "$target_check" -eq 1 ]]; then
    ((success_criteria++))
fi

trades_check=$(echo "$phase3_avg_trades <= 80" | bc -l 2>/dev/null || echo "1")
if [[ "$trades_check" -eq 1 ]]; then
    ((success_criteria++))
fi

success_percentage=$(echo "scale=1; $success_criteria * 100 / $total_criteria" | bc -l)

echo "Phase 3 Success Rate: ${success_criteria}/${total_criteria} criteria met (${success_percentage}%)" >> "$results_file"
echo "" >> "$results_file"

if [[ $success_criteria -eq 3 ]]; then
    echo "🏆 PHASE 3 RATING: A+ (EXCELLENT)" >> "$results_file"
    echo "   All success criteria achieved. Ready for live trading." >> "$results_file"
elif [[ $success_criteria -eq 2 ]]; then
    echo "🎯 PHASE 3 RATING: A- (VERY GOOD)" >> "$results_file"
    echo "   Major improvements achieved. Minor optimizations recommended." >> "$results_file"
elif [[ $success_criteria -eq 1 ]]; then
    echo "📊 PHASE 3 RATING: B+ (GOOD)" >> "$results_file"
    echo "   Significant progress made. Further refinement needed." >> "$results_file"
else
    echo "⚠️  PHASE 3 RATING: C (NEEDS IMPROVEMENT)" >> "$results_file"
    echo "   Fundamental issues remain. Major revision required." >> "$results_file"
fi

echo "" >> "$results_file"
echo "🚀 NEXT STEPS RECOMMENDATION:" >> "$results_file"
if [[ $success_criteria -ge 2 ]]; then
    echo "   • Consider live paper trading validation" >> "$results_file"
    echo "   • Monitor performance on fresh data" >> "$results_file"
    echo "   • Implement risk management protocols" >> "$results_file"
    echo "   • Set up real-time monitoring systems" >> "$results_file"
else
    echo "   • Analyze failure points for further optimization" >> "$results_file"
    echo "   • Consider alternative approaches" >> "$results_file"
    echo "   • Review market conditions during test period" >> "$results_file"
    echo "   • Implement additional risk controls" >> "$results_file"
fi

echo "" >> "$results_file"
echo "Analysis completed: $(date)" >> "$results_file"

echo ""
echo "✅ Phase 3 comprehensive testing complete!"
echo "📄 Detailed results saved to: $results_file"
echo ""
echo "📊 QUICK SUMMARY:"
echo "Phase 3 Profit: ${total_profits["PHASE_3"]} USDT"
echo "Negative Months: ${negative_months["PHASE_3"]}/6"
echo "Success Rate: ${success_criteria}/${total_criteria} criteria met"
echo ""
echo "💡 View detailed analysis: cat $results_file" 