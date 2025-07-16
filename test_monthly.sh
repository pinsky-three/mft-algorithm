#!/bin/bash

months=(
    "20250101-20250201"  # January 2025
    "20250201-20250301"  # February 2025  
    "20250301-20250401"  # March 2025
    "20250401-20250501"  # April 2025
    "20250501-20250601"  # May 2025
    "20250601-20250701"  # June 2025
    "20250701-20250715"  # July 2025 (partial)
)

# Test each month individually with optimized strategy and save results

month_names=(
    "January_2025"
    "February_2025"
    "March_2025" 
    "April_2025"
    "May_2025"
    "June_2025"
    "July_2025_partial"
)

# Output file for results
results_file="monthly_results_optimized.txt"

# Initialize results file
echo "🎯 OPTIMIZED STRATEGY - MONTHLY BACKTEST RESULTS" > "$results_file"
echo "=================================================================================" >> "$results_file"
echo "Strategy: CryptoScalpingOptimized v10 (Balanced Risk/Reward)" >> "$results_file"
echo "Pairs: BTC/USDT, ETH/USDT, SOL/USDT" >> "$results_file"
echo "Timeframe: 1m" >> "$results_file"
echo "Optimization: -2.5% stop loss, 2.5%/2%/1.5% ROI, regime filtering" >> "$results_file"
echo "Generated: $(date)" >> "$results_file"
echo "" >> "$results_file"

# Initialize summary variables
total_profit_usdt=0
total_trades=0

# Loop through each month
for i in "${!months[@]}"; do
    timerange="${months[$i]}"
    month_name="${month_names[$i]}"
    
    echo "🔄 Testing ${month_name} (${timerange})..."
    
    # Run backtest and capture output
    output=$(docker compose run --rm freqtrade backtesting -s CryptoScalpingOptimizedJuly -p BTC/USDT ETH/USDT SOL/USDT --timerange "$timerange" --fee 0.0002 --timeframe 1m 2>/dev/null | tr -d '\r')
    
    # Extract data with FIXED patterns matching exact freqtrade output
    profit_percent=$(echo "$output" | grep "│ Total profit %" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)%[[:space:]]*│.*/\1/')
    profit_usdt=$(echo "$output" | grep "│ Absolute profit" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)[[:space:]]*USDT[[:space:]]*│.*/\1/')
    total_trades_month=$(echo "$output" | grep "│ Total/Daily Avg Trades" | head -1 | sed 's/.*│[[:space:]]*\([0-9]*\)[[:space:]]*\/.*│.*/\1/')
    
    # Extract win rate from TOTAL row (already working correctly)
    win_rate=$(echo "$output" | grep "│    TOTAL │" | head -1 | sed 's/.*│[[:space:]]*[0-9]*[[:space:]]*[0-9]*[[:space:]]*[0-9]*[[:space:]]*\([0-9.]*\)[[:space:]]*│.*/\1/')
    
    # Extract ROI and stop loss counts from EXIT REASON STATS
    roi_exits=$(echo "$output" | grep "│[[:space:]]*roi[[:space:]]*│" | head -1 | awk -F'│' '{print $3}' | awk '{print $1}' | tr -d '\n\r')
    stop_losses=$(echo "$output" | grep "│[[:space:]]*stop_loss[[:space:]]*│" | head -1 | awk -F'│' '{print $3}' | awk '{print $1}' | tr -d '\n\r')
    
    # Extract max drawdown
    max_drawdown=$(echo "$output" | grep "│ Max % of account underwater" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)%[[:space:]]*│.*/\1/')
    
    # Handle empty/missing values
    profit_percent=${profit_percent:-"0.00"}
    profit_usdt=${profit_usdt:-"0.000"}
    total_trades_month=${total_trades_month:-"0"}
    win_rate=${win_rate:-"0.0"}
    roi_exits=${roi_exits:-"0"}
    stop_losses=${stop_losses:-"0"}
    max_drawdown=${max_drawdown:-"0.00"}
    
    # Clean up values (remove extra spaces, newlines)
    profit_percent=$(echo "$profit_percent" | tr -d '\n\r' | head -c 10)
    profit_usdt=$(echo "$profit_usdt" | tr -d '\n\r' | head -c 10)
    total_trades_month=$(echo "$total_trades_month" | tr -d '\n\r' | head -c 5)
    win_rate=$(echo "$win_rate" | tr -d '\n\r' | head -c 10)
    roi_exits=$(echo "$roi_exits" | tr -d '\n\r' | head -c 5)
    stop_losses=$(echo "$stop_losses" | tr -d '\n\r' | head -c 5)
    max_drawdown=$(echo "$max_drawdown" | tr -d '\n\r' | head -c 10)
    
    # Write to results file
    echo "📅 ${month_name} (${timerange})" >> "$results_file"
    echo "   Total Profit: ${profit_percent}% (${profit_usdt} USDT)" >> "$results_file"
    echo "   Trades: ${total_trades_month}" >> "$results_file"
    echo "   Win Rate: ${win_rate}%" >> "$results_file"
    echo "   📊 ROI exits: ${roi_exits}, Stop losses: ${stop_losses}, Drawdown: ${max_drawdown}%" >> "$results_file"
    echo "" >> "$results_file"
    
    # Add to summary (safe math)
    if [[ "$profit_usdt" =~ ^-?[0-9]+\.?[0-9]*$ ]]; then
        total_profit_usdt=$(echo "$total_profit_usdt + $profit_usdt" | bc -l 2>/dev/null || echo "$total_profit_usdt")
    fi
    if [[ "$total_trades_month" =~ ^[0-9]+$ ]]; then
        total_trades=$((total_trades + total_trades_month))
    fi
    
    echo "✅ ${month_name}: ${profit_percent}% (${profit_usdt} USDT), ${total_trades_month} trades, ${win_rate}% win rate"
done

# Calculate and write summary
echo "=================================================================================" >> "$results_file"
echo "📊 SUMMARY STATISTICS" >> "$results_file"
echo "=================================================================================" >> "$results_file"
echo "Total Period Profit: ${total_profit_usdt} USDT" >> "$results_file"
echo "Total Trades: ${total_trades}" >> "$results_file"

# Calculate average monthly profit
avg_monthly_profit=$(echo "scale=3; $total_profit_usdt / 6" | bc -l 2>/dev/null || echo "0.000")
echo "Average Monthly Profit: ${avg_monthly_profit} USDT" >> "$results_file"
echo "" >> "$results_file"

echo ""
echo "✅ Monthly backtest analysis complete!"
echo "📄 Results saved to: $results_file"
echo "💰 Total profit across all months: ${total_profit_usdt} USDT"
echo "📈 Total trades: ${total_trades}"
