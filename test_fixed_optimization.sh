#!/bin/bash

echo "🔧 FIXED AGGRESSIVE OPTIMIZATION - macOS Compatible"
echo "================================================="
echo "Target: 2% monthly profit (20 USDT/month)"
echo "Current best: 3.699 USDT/month validation (18.5% of target)"
echo ""

# Training and validation periods
TRAIN_PERIOD="20250101-20250501"
VALIDATION_PERIOD="20250501-20250701"

# Results file
results_file="fixed_optimization_results.txt"

# Initialize results
echo "🎯 FIXED OPTIMIZATION RESULTS - 2% MONTHLY TARGET" > "$results_file"
echo "=================================================" >> "$results_file"
echo "Training Period: $TRAIN_PERIOD" >> "$results_file"
echo "Validation Period: $VALIDATION_PERIOD" >> "$results_file"
echo "Target: 20 USDT/month (2% monthly profit)" >> "$results_file"
echo "Generated: $(date)" >> "$results_file"
echo "" >> "$results_file"

# Backup original strategy
cp user_data/strategies/CryptoScalpingOptimized.py user_data/strategies/CryptoScalpingOptimized_backup.py

# Test counter
test_count=0
best_monthly_profit=0
best_config=""
best_params=""

# Function to update strategy using Python (macOS compatible)
update_strategy_python() {
    local roi_immediate="$1"
    local roi_mid="$2" 
    local roi_final="$3"
    local stop_loss="$4"
    local min_market_health="$5"
    local min_volume_ratio="$6"
    local rsi_threshold="$7"
    local momentum_strength="$8"
    
    # Restore backup first
    cp user_data/strategies/CryptoScalpingOptimized_backup.py user_data/strategies/CryptoScalpingOptimized.py
    
    # Create Python script to modify parameters
    cat > temp_modify_strategy.py << EOF
import re

# Read the strategy file
with open('user_data/strategies/CryptoScalpingOptimized.py', 'r') as f:
    content = f.read()

# Update ROI ladder
content = re.sub(r'"0": 0\.030', f'"0": {roi_immediate}', content)
content = re.sub(r'"2": 0\.025', f'"2": {roi_mid}', content)
content = re.sub(r'"6": 0\.020', f'"6": {roi_final}', content)

# Update stop loss
content = re.sub(r'stoploss: float = -0\.025', f'stoploss: float = {stop_loss}', content)

# Update market health threshold
content = re.sub(r'MIN_MARKET_HEALTH = 0\.5', f'MIN_MARKET_HEALTH = {min_market_health}', content)

# Update volume ratio
content = re.sub(r'MIN_VOLUME_RATIO = 1\.9', f'MIN_VOLUME_RATIO = {min_volume_ratio}', content)

# Update RSI threshold
content = re.sub(r'RSI_THRESHOLD = 57', f'RSI_THRESHOLD = {rsi_threshold}', content)

# Update momentum strength
content = re.sub(r'MOMENTUM_STRENGTH = 0\.78', f'MOMENTUM_STRENGTH = {momentum_strength}', content)

# Write back the modified content
with open('user_data/strategies/CryptoScalpingOptimized.py', 'w') as f:
    f.write(content)

print(f"Updated strategy with ROI: {roi_immediate}/{roi_mid}/{roi_final}, Stop: {stop_loss}")
EOF
    
    # Run the Python script
    python temp_modify_strategy.py
    rm temp_modify_strategy.py
}

# Function to run test
run_optimization_test() {
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
    
    # Only validate if training shows promise (>2 USDT/month)
    if (( $(echo "$train_monthly_profit > 2.0" | bc -l 2>/dev/null) )); then
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

echo "🔬 Starting Fixed Parameter Testing..."
echo ""

# === FOCUSED HIGH-IMPACT TESTS ===

echo "📈 FOCUSED HIGH-IMPACT OPTIMIZATION TESTS"

# Test 1: Current baseline (verify it works)
update_strategy_python 0.030 0.025 0.020 -0.025 0.5 1.9 57 0.78
run_optimization_test "Current_Baseline" "Current parameters (baseline verification)"

# Test 2: Ultra-Aggressive ROI
update_strategy_python 0.060 0.045 0.030 -0.025 0.5 1.9 57 0.78
run_optimization_test "Ultra_Aggressive_ROI" "ROI: 6.0%/4.5%/3.0%, Stop: -2.5%"

# Test 3: Aggressive ROI + Tight Stop
update_strategy_python 0.050 0.040 0.030 -0.015 0.5 1.9 57 0.78
run_optimization_test "Aggressive_Tight_Stop" "ROI: 5.0%/4.0%/3.0%, Stop: -1.5%"

# Test 4: More Trades (Relaxed Filters)
update_strategy_python 0.040 0.030 0.025 -0.025 0.3 1.5 52 0.65
run_optimization_test "High_Frequency" "ROI: 4.0%/3.0%/2.5%, Relaxed for +trades"

# Test 5: Quality over Quantity
update_strategy_python 0.070 0.050 0.035 -0.020 0.7 2.2 65 0.85
run_optimization_test "Quality_Focus" "ROI: 7.0%/5.0%/3.5%, Ultra-conservative entry"

# Test 6: Balanced Aggressive
update_strategy_python 0.045 0.035 0.025 -0.020 0.4 1.7 55 0.75
run_optimization_test "Balanced_Aggressive" "ROI: 4.5%/3.5%/2.5%, Moderate thresholds"

# === RESULTS SUMMARY ===
echo ""
echo "========================================================="
echo "🏆 FIXED OPTIMIZATION COMPLETE - RESULTS SUMMARY"
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
echo "🔄 Original strategy restored. Ready for deployment if desired." 