#!/bin/bash

echo "📊 MONTHLY PERFORMANCE ANALYSIS - ROI-Only Strategy"
echo "===================================================="
echo ""
echo "🎯 GOAL: Analyze monthly consistency for 3% monthly target"
echo "📈 Current: +0.28% over 6 months → Need 3% per month"
echo ""

# Test each month individually
months=(
    "20250101-20250201"  # January 2025
    "20250201-20250301"  # February 2025  
    "20250301-20250401"  # March 2025
    "20250401-20250501"  # April 2025
    "20250501-20250601"  # May 2025
    "20250601-20250701"  # June 2025
    "20250701-20250710"  # July 2025 (partial)
)

month_names=(
    "January_2025"
    "February_2025"
    "March_2025" 
    "April_2025"
    "May_2025"
    "June_2025"
    "July_2025_partial"
)

echo "🗓️  TESTING MONTHLY WINDOWS:"
echo ""

for i in "${!months[@]}"; do
    timerange="${months[$i]}"
    month_name="${month_names[$i]}"
    
    echo "📅 Testing ${month_name} (${timerange})..."
    
    docker compose run --rm freqtrade backtesting \
      -s CryptoScalpingOptimized \
      -p BTC/USDT \
      --timerange ${timerange} \
      --fee 0.0002 \
      --timeframe 5m \
      --export trades \
      --export-filename user_data/backtest_results/monthly_${month_name}.json \
      2>/dev/null | grep -E "(BACKTESTING REPORT|Total profit %|Win%|Trades)" | head -10
    
    echo ""
    echo "----------------------------------------"
    echo ""
done

echo ""
echo "🏆 MONTHLY ANALYSIS COMPLETE!"
echo ""
echo "📊 ANALYZE RESULTS FOR:"
echo "   📈 Best performing months (target: +3%)"
echo "   📉 Worst performing months" 
echo "   🎯 Consistency across months"
echo "   📊 Trade frequency per month"
echo "   💡 Patterns for optimization"
echo ""
echo "🎯 NEXT STEPS:"
echo "   1. Identify what makes good months profitable"
echo "   2. Optimize parameters for 3% monthly target"
echo "   3. Test optimized strategy across all months"
echo "   4. Validate consistent 3% monthly performance" 