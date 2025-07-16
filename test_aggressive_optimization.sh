#!/bin/bash

echo "🚀 AGGRESSIVE HYPERPARAMETER OPTIMIZATION FOR 2% MONTHLY TARGET"
echo "============================================================="
echo "Current Performance: ~0.4% monthly (23.845 USDT over 6 months)"
echo "Target Performance: 2.0% monthly (120+ USDT over 6 months - 5x improvement)"
echo "Strategy: Test aggressive parameter combinations systematically"
echo ""

# Training period (Jan-May 2025)
TRAIN_PERIOD="20250101-20250501"
# Validation period (May-June 2025)  
VALIDATION_PERIOD="20250501-20250701"

# Results file
results_file="aggressive_optimization_results.txt"

# Initialize results
echo "🎯 AGGRESSIVE OPTIMIZATION RESULTS - 2% MONTHLY TARGET" > "$results_file"
echo "=========================================================" >> "$results_file"
echo "Training Period: $TRAIN_PERIOD" >> "$results_file"
echo "Validation Period: $VALIDATION_PERIOD" >> "$results_file"
echo "Target: 2% monthly profit (5x current performance)" >> "$results_file"
echo "Generated: $(date)" >> "$results_file"
echo "" >> "$results_file"

# Backup original strategy
cp user_data/strategies/CryptoScalpingOptimized.py user_data/strategies/CryptoScalpingOptimized_backup.py

# Test configuration counter
test_count=0
best_monthly_profit=0
best_config=""
best_params=""

# Function to run backtest and extract monthly profit
run_aggressive_test() {
    local config_name="$1"
    local params_desc="$2"
    
    test_count=$((test_count + 1))
    echo ""
    echo "🔬 Test #$test_count: $config_name"
    echo "Parameters: $params_desc"
    
    # Run training backtest
    echo "   📊 Training backtest ($TRAIN_PERIOD)..."
    training_output=$(docker compose run --rm freqtrade backtesting -s CryptoScalpingOptimized -p BTC/USDT ETH/USDT SOL/USDT --timerange "$TRAIN_PERIOD" --fee 0.0002 --timeframe 1m 2>/dev/null | tr -d '\r')
    
    # Extract training results
    train_profit_usdt=$(echo "$training_output" | grep "│ Absolute profit" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)[[:space:]]*USDT[[:space:]]*│.*/\1/')
    train_trades=$(echo "$training_output" | grep "│ Total/Daily Avg Trades" | head -1 | sed 's/.*│[[:space:]]*\([0-9]*\)[[:space:]]*\/.*│.*/\1/')
    train_win_rate=$(echo "$training_output" | grep "│    TOTAL │" | head -1 | sed 's/.*│[[:space:]]*[0-9]*[[:space:]]*[0-9]*[[:space:]]*[0-9]*[[:space:]]*\([0-9.]*\)[[:space:]]*│.*/\1/')
    
    # Clean values
    train_profit_usdt=${train_profit_usdt:-"0.000"}
    train_trades=${train_trades:-"0"}
    train_win_rate=${train_win_rate:-"0.0"}
    
    # Calculate monthly profit (4 months in training period)
    train_monthly_profit=$(echo "scale=3; $train_profit_usdt / 4" | bc -l 2>/dev/null || echo "0.000")
    
    echo "   💰 Training: $train_profit_usdt USDT ($train_monthly_profit USDT/month), $train_trades trades, $train_win_rate% win rate"
    
    # Only validate if training shows promise (>0.8 USDT/month)
    if (( $(echo "$train_monthly_profit > 0.8" | bc -l 2>/dev/null) )); then
        echo "   ✅ Promising training results - running validation..."
        
        # Run validation backtest
        validation_output=$(docker compose run --rm freqtrade backtesting -s CryptoScalpingOptimized -p BTC/USDT ETH/USDT SOL/USDT --timerange "$VALIDATION_PERIOD" --fee 0.0002 --timeframe 1m 2>/dev/null | tr -d '\r')
        
        # Extract validation results
        val_profit_usdt=$(echo "$validation_output" | grep "│ Absolute profit" | head -1 | sed 's/.*│[[:space:]]*\([0-9.-]*\)[[:space:]]*USDT[[:space:]]*│.*/\1/')
        val_trades=$(echo "$validation_output" | grep "│ Total/Daily Avg Trades" | head -1 | sed 's/.*│[[:space:]]*\([0-9]*\)[[:space:]]*\/.*│.*/\1/')
        val_win_rate=$(echo "$validation_output" | grep "│    TOTAL │" | head -1 | sed 's/.*│[[:space:]]*[0-9]*[[:space:]]*[0-9]*[[:space:]]*\([0-9.]*\)[[:space:]]*│.*/\1/')
        
        # Clean values
        val_profit_usdt=${val_profit_usdt:-"0.000"}
        val_trades=${val_trades:-"0"}
        val_win_rate=${val_win_rate:-"0.0"}
        
        # Calculate monthly profit (2 months in validation period)
        val_monthly_profit=$(echo "scale=3; $val_profit_usdt / 2" | bc -l 2>/dev/null || echo "0.000")
        
        echo "   📈 Validation: $val_profit_usdt USDT ($val_monthly_profit USDT/month), $val_trades trades, $val_win_rate% win rate"
        
        # Check if this is the best configuration so far
        if (( $(echo "$val_monthly_profit > $best_monthly_profit" | bc -l 2>/dev/null) )); then
            best_monthly_profit="$val_monthly_profit"
            best_config="$config_name"
            best_params="$params_desc"
            echo "   🏆 NEW BEST CONFIGURATION!"
        fi
        
        # Log results
        echo "📊 Test #$test_count: $config_name" >> "$results_file"
        echo "   Parameters: $params_desc" >> "$results_file"
        echo "   Training: $train_profit_usdt USDT ($train_monthly_profit/month), $train_trades trades, $train_win_rate% win rate" >> "$results_file"
        echo "   Validation: $val_profit_usdt USDT ($val_monthly_profit/month), $val_trades trades, $val_win_rate% win rate" >> "$results_file"
        echo "" >> "$results_file"
        
    else
        echo "   ❌ Poor training results - skipping validation"
        echo "📊 Test #$test_count: $config_name - TRAINING FAILED" >> "$results_file"
        echo "   Parameters: $params_desc" >> "$results_file"
        echo "   Training: $train_profit_usdt USDT ($train_monthly_profit/month) - Below threshold" >> "$results_file"
        echo "" >> "$results_file"
    fi
}

# Function to update strategy parameters
update_strategy() {
    local roi_immediate="$1"
    local roi_mid="$2" 
    local roi_final="$3"
    local stop_loss="$4"
    local min_market_health="$5"
    local min_volume_ratio="$6"
    local rsi_threshold="$7"
    local momentum_strength="$8"
    
    # Restore backup
    cp user_data/strategies/CryptoScalpingOptimized_backup.py user_data/strategies/CryptoScalpingOptimized.py
    
    # Update ROI ladder
    sed -i "s/\"0\": 0.030/\"0\": $roi_immediate/g" user_data/strategies/CryptoScalpingOptimized.py
    sed -i "s/\"2\": 0.025/\"2\": $roi_mid/g" user_data/strategies/CryptoScalpingOptimized.py
    sed -i "s/\"6\": 0.020/\"6\": $roi_final/g" user_data/strategies/CryptoScalpingOptimized.py
    
    # Update stop loss
    sed -i "s/stoploss: float = -0.025/stoploss: float = $stop_loss/g" user_data/strategies/CryptoScalpingOptimized.py
    
    # Update market health threshold
    sed -i "s/MIN_MARKET_HEALTH = 0.5/MIN_MARKET_HEALTH = $min_market_health/g" user_data/strategies/CryptoScalpingOptimized.py
    
    # Update volume ratio
    sed -i "s/MIN_VOLUME_RATIO = 1.9/MIN_VOLUME_RATIO = $min_volume_ratio/g" user_data/strategies/CryptoScalpingOptimized.py
    
    # Update RSI threshold
    sed -i "s/RSI_THRESHOLD = 57/RSI_THRESHOLD = $rsi_threshold/g" user_data/strategies/CryptoScalpingOptimized.py
    
    # Update momentum strength
    sed -i "s/MOMENTUM_STRENGTH = 0.78/MOMENTUM_STRENGTH = $momentum_strength/g" user_data/strategies/CryptoScalpingOptimized.py
}

echo "🔬 Starting Aggressive Parameter Testing..."
echo ""

# === TEST SUITE 1: AGGRESSIVE ROI TARGETS ===
echo "📈 TEST SUITE 1: AGGRESSIVE ROI TARGETS"

# Test 1: Super Aggressive ROI (5%/4%/3.5%)
update_strategy 0.050 0.040 0.035 -0.025 0.5 1.9 57 0.78
run_aggressive_test "Super_Aggressive_ROI" "ROI: 5.0%/4.0%/3.5%, Stop: -2.5%"

# Test 2: Very Aggressive ROI (4.5%/3.5%/3%)
update_strategy 0.045 0.035 0.030 -0.025 0.5 1.9 57 0.78  
run_aggressive_test "Very_Aggressive_ROI" "ROI: 4.5%/3.5%/3.0%, Stop: -2.5%"

# Test 3: Moderate Aggressive ROI (4%/3%/2.5%)
update_strategy 0.040 0.030 0.025 -0.025 0.5 1.9 57 0.78
run_aggressive_test "Moderate_Aggressive_ROI" "ROI: 4.0%/3.0%/2.5%, Stop: -2.5%"

# === TEST SUITE 2: TIGHTER STOP LOSS + AGGRESSIVE ROI ===
echo ""
echo "🛡️ TEST SUITE 2: RISK-ADJUSTED AGGRESSIVE"

# Test 4: Aggressive ROI + Tight Stop (4%/3%/2.5% + 2% stop)
update_strategy 0.040 0.030 0.025 -0.020 0.5 1.9 57 0.78
run_aggressive_test "Aggressive_Tight_Stop" "ROI: 4.0%/3.0%/2.5%, Stop: -2.0%"

# Test 5: Very Aggressive ROI + Very Tight Stop (5%/4%/3% + 1.5% stop)
update_strategy 0.050 0.040 0.030 -0.015 0.5 1.9 57 0.78
run_aggressive_test "Very_Aggressive_Very_Tight" "ROI: 5.0%/4.0%/3.0%, Stop: -1.5%"

# === TEST SUITE 3: RELAXED MARKET HEALTH FOR MORE TRADES ===
echo ""
echo "📊 TEST SUITE 3: INCREASED TRADE FREQUENCY"

# Test 6: Aggressive ROI + Relaxed Market Health (more trades)
update_strategy 0.040 0.030 0.025 -0.025 0.3 1.6 55 0.70
run_aggressive_test "High_Frequency_Aggressive" "ROI: 4.0%/3.0%/2.5%, Relaxed filters for +trades"

# Test 7: Super Relaxed for Maximum Trades
update_strategy 0.045 0.035 0.025 -0.025 0.2 1.4 52 0.65
run_aggressive_test "Maximum_Frequency" "ROI: 4.5%/3.5%/2.5%, Very relaxed for max trades"

# === TEST SUITE 4: HYBRID APPROACHES ===
echo ""
echo "🔄 TEST SUITE 4: HYBRID STRATEGIES"

# Test 8: Balanced Aggressive (moderate ROI + relaxed filters)
update_strategy 0.035 0.025 0.020 -0.025 0.35 1.7 56 0.72
run_aggressive_test "Balanced_Aggressive" "ROI: 3.5%/2.5%/2.0%, Moderate relaxation"

# Test 9: ETH-Focused Optimization (ETH showed 76.5% win rate)
update_strategy 0.040 0.030 0.025 -0.020 0.4 1.8 55 0.75
run_aggressive_test "ETH_Focused_Aggressive" "ROI: 4.0%/3.0%/2.5%, ETH-optimized thresholds"

# Test 10: Ultra-Conservative Entry + Ultra-Aggressive Exit
update_strategy 0.060 0.045 0.030 -0.025 0.7 2.2 62 0.85
run_aggressive_test "Conservative_Entry_Aggressive_Exit" "ROI: 6.0%/4.5%/3.0%, Ultra-conservative entry"

# === RESULTS SUMMARY ===
echo ""
echo "========================================================="
echo "🏆 OPTIMIZATION COMPLETE - RESULTS SUMMARY"
echo "========================================================="
echo ""
echo "Best Configuration: $best_config"
echo "Best Monthly Profit: $best_monthly_profit USDT/month"
echo "Target Achievement: $(echo "scale=1; $best_monthly_profit / 20 * 100" | bc -l 2>/dev/null || echo "0")% of 2% monthly target"
echo "Best Parameters: $best_params"
echo ""

# Write summary to results file
echo "=========================================================" >> "$results_file"
echo "🏆 OPTIMIZATION SUMMARY" >> "$results_file"
echo "=========================================================" >> "$results_file"
echo "Total Tests Conducted: $test_count" >> "$results_file"
echo "Best Configuration: $best_config" >> "$results_file"
echo "Best Monthly Profit: $best_monthly_profit USDT/month" >> "$results_file"
echo "Target Achievement: $(echo "scale=1; $best_monthly_profit / 20 * 100" | bc -l 2>/dev/null || echo "0")% of 2% monthly target (20 USDT/month)" >> "$results_file"
echo "Best Parameters: $best_params" >> "$results_file"
echo "" >> "$results_file"

if (( $(echo "$best_monthly_profit > 15" | bc -l 2>/dev/null) )); then
    echo "🎯 SUCCESS: Configuration achieves >75% of monthly target!" >> "$results_file"
    echo "💡 Recommendation: Deploy best configuration for comprehensive testing" >> "$results_file"
elif (( $(echo "$best_monthly_profit > 10" | bc -l 2>/dev/null) )); then
    echo "📈 PROGRESS: Configuration achieves >50% of monthly target" >> "$results_file"
    echo "💡 Recommendation: Consider further optimization or risk adjustment" >> "$results_file"
else
    echo "❌ CHALLENGE: No configuration achieved >50% of monthly target" >> "$results_file"
    echo "💡 Recommendation: Consider fundamental strategy changes beyond parameter tuning" >> "$results_file"
fi

echo "📄 Detailed results saved to: $results_file"

# Restore original strategy
cp user_data/strategies/CryptoScalpingOptimized_backup.py user_data/strategies/CryptoScalpingOptimized.py

echo ""
echo "🔄 Original strategy restored. Ready for deployment of best configuration if desired." 