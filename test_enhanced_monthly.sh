#!/bin/bash

echo "🚀 ENHANCED STRATEGY v7 - 3% MONTHLY TARGET TEST"
echo "================================================="
echo ""
echo "🎯 TARGET: 3% monthly return (36% annual compound)"
echo "📊 Enhanced ROI: 2.0%/1.5%/1.0% (vs 1.2%/0.8%/0.4%)"
echo "⚡ Premium setups: Higher quality, tighter filters"
echo ""

echo "🔬 FULL PERIOD TEST (Jan-July 2025):"
echo "======================================"

docker compose run --rm freqtrade backtesting \
  -s CryptoScalpingOptimized \
  -p BTC/USDT \
  --timerange 20250101-20250712 \
  --fee 0.0002 \
  --timeframe 5m \
  --export trades \
  --export-filename user_data/backtest_results/enhanced_v7_full_period.json

echo ""
echo "📅 MONTHLY BREAKDOWN TEST:"
echo "=========================="

# Test each month individually with enhanced strategy
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

echo ""
monthly_results=""

for i in "${!months[@]}"; do
    timerange="${months[$i]}"
    month_name="${month_names[$i]}"
    
    echo "📅 Enhanced Test: ${month_name} (${timerange})..."
    
    result=$(docker compose run --rm freqtrade backtesting \
      -s CryptoScalpingOptimized \
      -p BTC/USDT \
      --timerange ${timerange} \
      --fee 0.0002 \
      --timeframe 5m \
      --export trades \
      --export-filename user_data/backtest_results/enhanced_monthly_${month_name}.json \
      2>/dev/null | grep "Total profit %" | tail -1)
    
    profit=$(echo "$result" | grep -o "[-0-9.]*%" | head -1)
    monthly_results="${monthly_results}${month_name}: ${profit}\n"
    
    echo "   Result: ${profit}"
    echo ""
done

echo ""
echo "🏆 ENHANCED STRATEGY v7 MONTHLY SUMMARY:"
echo "========================================"
echo -e "$monthly_results"
echo ""
echo "🎯 TARGET ANALYSIS:"
echo "   🟢 Months >= 3%: Target achieved!"
echo "   🟡 Months 1-3%: Close to target"  
echo "   🔴 Months < 1%: Need more optimization"
echo ""
echo "📊 ENHANCEMENT SUCCESS METRICS:"
echo "   ✅ Higher ROI targets (2.0%/1.5%/1.0%)"
echo "   ✅ Premium quality setups only"
echo "   ✅ Tighter risk management (6% stoploss)"
echo "   ✅ Enhanced entry filters"
echo ""
echo "🏆 MISSION: CONSISTENT 3% MONTHLY RETURNS!"
echo "💎 Quality over quantity = Higher monthly profits" 