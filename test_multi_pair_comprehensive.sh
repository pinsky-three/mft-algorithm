#!/bin/bash

echo "🚀 MULTI-PAIR COMPREHENSIVE TESTING - 3% MONTHLY TARGET"
echo "======================================================="
echo ""
echo "🎯 GOAL: Test if multiple pairs can achieve 3% monthly returns"
echo "📈 Pairs: BTC/USDT + ETH/USDT + SOL/USDT (3x opportunities)"
echo "⏰ Timeframe: 5m (current strategy optimized for this)"
echo "🎪 Strategy: Ultra-aggressive ROI-only v8"
echo ""

# Test period (focus on best performing period first)
TEST_PERIOD="20250401-20250501"  # April 2025 (best month for BTC)
echo "📅 Test Period: April 2025 (best performing month)"
echo ""

echo "🔬 INDIVIDUAL PAIR TESTING:"
echo "==========================="

declare -a pairs=("BTC/USDT" "ETH/USDT" "SOL/USDT")
declare -A results

for pair in "${pairs[@]}"; do
    echo ""
    echo "📊 Testing ${pair}..."
    
    # Run backtest and capture key metrics
    result=$(docker compose run --rm freqtrade backtesting \
        -s CryptoScalpingOptimized \
        -p "${pair}" \
        --timerange ${TEST_PERIOD} \
        --fee 0.0002 \
        --timeframe 5m \
        --export trades \
        --export-filename "user_data/backtest_results/multi_${pair//\//_}_april.json" \
        2>/dev/null)
    
    # Extract key metrics
    trades=$(echo "$result" | grep "Total/Daily Avg Trades" | head -1 | grep -o "[0-9]\+")
    profit=$(echo "$result" | grep "Total profit %" | head -1 | grep -o "[-0-9.]\+%")
    win_rate=$(echo "$result" | grep -o "[0-9.]\+%" | tail -1)
    
    echo "   📈 ${pair}: ${trades} trades, ${win_rate} win rate, ${profit} profit"
    
    # Store results
    results["${pair}_trades"]="$trades"
    results["${pair}_profit"]="$profit"
    results["${pair}_win_rate"]="$win_rate"
done

echo ""
echo "🎯 MULTI-PAIR COMBINED TESTING:"
echo "==============================="

# Test all pairs together
echo ""
echo "🔥 Testing ALL PAIRS COMBINED (BTC + ETH + SOL)..."

combined_result=$(docker compose run --rm freqtrade backtesting \
    -s CryptoScalpingOptimized \
    -p BTC/USDT ETH/USDT SOL/USDT \
    --timerange ${TEST_PERIOD} \
    --fee 0.0002 \
    --timeframe 5m \
    --export trades \
    --export-filename "user_data/backtest_results/multi_all_pairs_april.json")

echo ""
echo "🏆 MULTI-PAIR RESULTS SUMMARY:"
echo "=============================="

# Extract combined results
combined_trades=$(echo "$combined_result" | grep "Total/Daily Avg Trades" | head -1 | grep -o "[0-9]\+" | head -1)
combined_profit=$(echo "$combined_result" | grep "Total profit %" | head -1 | grep -o "[-0-9.]\+%")
combined_win_rate=$(echo "$combined_result" | grep "Win%" | tail -1 | grep -o "[0-9.]\+")

echo ""
echo "📊 INDIVIDUAL PAIR PERFORMANCE:"
for pair in "${pairs[@]}"; do
    trades_key="${pair}_trades"
    profit_key="${pair}_profit"
    win_rate_key="${pair}_win_rate"
    echo "   ${pair}: ${results[$trades_key]} trades, ${results[$win_rate_key]} win rate, ${results[$profit_key]} profit"
done

echo ""
echo "🔥 COMBINED PERFORMANCE (ALL PAIRS):"
echo "   Total Trades: ${combined_trades}"
echo "   Combined Profit: ${combined_profit}"
echo "   Combined Win Rate: ${combined_win_rate}%"

echo ""
echo "🎯 3% MONTHLY TARGET ANALYSIS:"
echo "============================="

# Convert profit to numeric for comparison
combined_profit_num=$(echo "$combined_profit" | sed 's/%//')

if (( $(echo "$combined_profit_num >= 3.0" | bc -l) )); then
    echo "   🟢 TARGET ACHIEVED! ${combined_profit} >= 3.0%"
    echo "   🏆 Multi-pair strategy SUCCESS!"
elif (( $(echo "$combined_profit_num >= 1.0" | bc -l) )); then
    echo "   🟡 GOOD PROGRESS! ${combined_profit} (need 3.0%)"
    echo "   📈 ${combined_profit_num}x improvement from single pair needed"
else
    echo "   🔴 BELOW TARGET: ${combined_profit} (need 3.0%)"
    echo "   📈 More optimization or different approach needed"
fi

echo ""
echo "🚀 SCALING ANALYSIS:"
echo "==================="

# Calculate scaling factor
single_btc_profit=$(echo "${results[BTC/USDT_profit]}" | sed 's/%//')
scaling_factor=$(echo "scale=2; $combined_profit_num / $single_btc_profit" | bc -l)

echo "   📊 Single BTC: ${results[BTC/USDT_profit]}"
echo "   📊 Multi-pair: ${combined_profit}"
echo "   📈 Scaling Factor: ${scaling_factor}x"

if (( $(echo "$scaling_factor >= 2.5" | bc -l) )); then
    echo "   ✅ EXCELLENT scaling! Multi-pair adds significant value"
elif (( $(echo "$scaling_factor >= 1.5" | bc -l) )); then
    echo "   🟡 GOOD scaling! Multi-pair provides decent improvement"
else
    echo "   🔴 POOR scaling! Multi-pair not adding much value"
fi

echo ""
echo "🎯 RECOMMENDATIONS:"
echo "=================="

if (( $(echo "$combined_profit_num >= 3.0" | bc -l) )); then
    echo "   🏆 SUCCESS! Multi-pair strategy achieves 3% monthly target"
    echo "   📈 DEPLOY: Use BTC+ETH+SOL with ultra-aggressive ROI strategy"
    echo "   🔄 VALIDATE: Test on other months for consistency"
elif (( $(echo "$combined_profit_num >= 1.0" | bc -l) )); then
    echo "   📈 PROMISING! Close to target with multi-pair approach"
    echo "   🔧 OPTIMIZE: Try 1m timeframe for more opportunities"
    echo "   🎯 ENHANCE: Further tune ROI targets or add more pairs"
else
    echo "   🔄 PIVOT: Multi-pair 5m scalping may not reach 3% monthly"
    echo "   🎯 ALTERNATIVES: Try 1m timeframe or swing trading approach"
    echo "   📊 REALITY CHECK: 1% monthly (12% annual) may be more realistic"
fi

echo ""
echo "🏆 MULTI-PAIR TESTING COMPLETE!"
echo "Next: Test different timeframes (1m, 15m) if needed" 