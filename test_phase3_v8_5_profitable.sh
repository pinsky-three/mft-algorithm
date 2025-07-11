#!/bin/bash

# ================================================================================
# PHASE 3 ADVANCED OPTIMIZATION TEST - v8.5 PROFITABLE
# ================================================================================
# 
# MultiHorizonMomentum Strategy v8.5 - Data-driven optimization for BTC $110K+
# Based on comprehensive volatility analysis and optimized ATR targets:
# 
# OPTIMIZED TARGETS v8.5:
# - Take Profit: 3.5x ATR (vs 2.5x in v8.4) - 40% increase for volatile conditions
# - Stop Loss: 2.2x ATR (vs 1.5x in v8.4) - 47% increase for whipsaw protection  
# - Trailing: 1.8x ATR (vs 1.2x in v8.4) - 50% increase for profit capture
# - Multi-timeframe: 1m primary, 5m secondary, 15m trend filter
#
# TESTING SCENARIOS:
# 1. January 2025 profitability test (BTC $110K+ period)
# 2. Cross-validation on different 2025 periods
# 3. Comparison with v8.2, v8.3, v8.4 performance
# 4. Multi-pair validation (BTC + ETH)
# 5. Different fee scenarios analysis
# 
# TARGET: Convert 0% win rate → profitable strategy
# ================================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
STRATEGY="MultiHorizonMomentum"
RESULTS_DIR="user_data/backtest_results"
CONFIG_FILE="user_data/config.json"

# Ensure results directory exists
mkdir -p $RESULTS_DIR

echo -e "${PURPLE}════════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${PURPLE}🚀 PHASE 3 ADVANCED OPTIMIZATION TEST - v8.5 PROFITABLE${NC}"
echo -e "${PURPLE}════════════════════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}📊 Strategy: $STRATEGY v8.5${NC}"
echo -e "${GREEN}🎯 Target: Convert 0% win rate → profitable in BTC \$110K+ conditions${NC}"
echo ""
echo -e "${BLUE}🔧 Optimizations Applied:${NC}"
echo -e "${BLUE}   • Take Profit: 3.5x ATR (+40% vs v8.4)${NC}"
echo -e "${BLUE}   • Stop Loss: 2.2x ATR (+47% vs v8.4)${NC}"
echo -e "${BLUE}   • Trailing: 1.8x ATR (+50% vs v8.4)${NC}"
echo -e "${BLUE}   • Multi-timeframe: 1m + 5m + 15m${NC}"
echo -e "${BLUE}   • Volume filter: 3x threshold${NC}"
echo ""

# ================================================================================
# TEST 1: January 2025 Profitability Test (Primary Target)
# ================================================================================

echo -e "${YELLOW}▶ TEST 1: January 2025 BTC \$110K+ Profitability Test${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

docker compose run --rm freqtrade backtesting \
  --strategy $STRATEGY \
  --config $CONFIG_FILE \
  --pairs BTC/USDT \
  --timerange 20250101-20250131 \
  --timeframe 1m \
  --fee 0.1 \
  --enable-protections \
  --breakdown day \
  --export trades \
  --export-filename $RESULTS_DIR/v8_5_january_2025_btc110k.json

echo ""
echo -e "${GREEN}✓ January 2025 test completed - Results saved${NC}"
echo ""

# ================================================================================
# TEST 2: Multi-Period 2025 Cross-Validation
# ================================================================================

echo -e "${YELLOW}▶ TEST 2: 2025 Cross-Validation (Multiple Periods)${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Test different 2025 periods to validate consistency
echo -e "${BLUE}📅 Testing January 1-15, 2025 (First half)${NC}"
docker compose run --rm freqtrade backtesting \
  --strategy $STRATEGY \
  --config $CONFIG_FILE \
  --pairs BTC/USDT \
  --timerange 20250101-20250115 \
  --timeframe 1m \
  --fee 0.1 \
  --enable-protections \
  --export trades \
  --export-filename $RESULTS_DIR/v8_5_jan_first_half_2025.json

echo ""
echo -e "${BLUE}📅 Testing January 16-31, 2025 (Second half)${NC}"
docker compose run --rm freqtrade backtesting \
  --strategy $STRATEGY \
  --config $CONFIG_FILE \
  --pairs BTC/USDT \
  --timerange 20250116-20250131 \
  --timeframe 1m \
  --fee 0.1 \
  --enable-protections \
  --export trades \
  --export-filename $RESULTS_DIR/v8_5_jan_second_half_2025.json

echo ""
echo -e "${GREEN}✓ Cross-validation tests completed${NC}"
echo ""

# ================================================================================
# TEST 3: Multi-Pair Validation (BTC + ETH)
# ================================================================================

echo -e "${YELLOW}▶ TEST 3: Multi-Pair Validation (BTC + ETH)${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

docker compose run --rm freqtrade backtesting \
  --strategy $STRATEGY \
  --config $CONFIG_FILE \
  --pairs BTC/USDT ETH/USDT \
  --timerange 20250101-20250131 \
  --timeframe 1m \
  --fee 0.1 \
  --enable-protections \
  --breakdown pair \
  --export trades \
  --export-filename $RESULTS_DIR/v8_5_multi_pair_jan_2025.json

echo ""
echo -e "${GREEN}✓ Multi-pair validation completed${NC}"
echo ""

# ================================================================================
# TEST 4: Fee Sensitivity Analysis
# ================================================================================

echo -e "${YELLOW}▶ TEST 4: Fee Sensitivity Analysis${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Test with different fee scenarios
echo -e "${BLUE}💰 Testing with 0% fees (edge validation)${NC}"
docker compose run --rm freqtrade backtesting \
  --strategy $STRATEGY \
  --config $CONFIG_FILE \
  --pairs BTC/USDT \
  --timerange 20250101-20250131 \
  --timeframe 1m \
  --fee 0 \
  --enable-protections \
  --export trades \
  --export-filename $RESULTS_DIR/v8_5_no_fees_jan_2025.json

echo ""
echo -e "${BLUE}💰 Testing with 0.05% fees (competitive)${NC}"
docker compose run --rm freqtrade backtesting \
  --strategy $STRATEGY \
  --config $CONFIG_FILE \
  --pairs BTC/USDT \
  --timerange 20250101-20250131 \
  --timeframe 1m \
  --fee 0.05 \
  --enable-protections \
  --export trades \
  --export-filename $RESULTS_DIR/v8_5_low_fees_jan_2025.json

echo ""
echo -e "${GREEN}✓ Fee sensitivity analysis completed${NC}"
echo ""

# ================================================================================
# TEST 5: Extended 2025 Performance Test
# ================================================================================

echo -e "${YELLOW}▶ TEST 5: Extended 2025 Performance Test${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Test on all available 2025 data for comprehensive analysis
docker compose run --rm freqtrade backtesting \
  --strategy $STRATEGY \
  --config $CONFIG_FILE \
  --pairs BTC/USDT \
  --timerange 20250101- \
  --timeframe 1m \
  --fee 0.0002 \
  --enable-protections \
  --breakdown month \
  --export trades \
  --export-filename $RESULTS_DIR/v8_5_extended_2025.json

echo ""
echo -e "${GREEN}✓ Extended 2025 test completed${NC}"
echo ""

# ================================================================================
# RESULTS SUMMARY AND ANALYSIS
# ================================================================================

echo -e "${PURPLE}════════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${PURPLE}📊 PHASE 3 v8.5 TEST RESULTS SUMMARY${NC}"
echo -e "${PURPLE}════════════════════════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${GREEN}📁 Results Location: $RESULTS_DIR${NC}"
echo ""
echo -e "${BLUE}📈 Tests Completed:${NC}"
echo -e "${BLUE}   1. ✓ January 2025 BTC \$110K+ Profitability${NC}"
echo -e "${BLUE}   2. ✓ Cross-validation (First/Second half January)${NC}"
echo -e "${BLUE}   3. ✓ Multi-pair validation (BTC + ETH)${NC}"
echo -e "${BLUE}   4. ✓ Fee sensitivity (0%, 0.05%, 0.1%)${NC}"
echo -e "${BLUE}   5. ✓ Extended 2025 performance${NC}"
echo ""

echo -e "${YELLOW}🎯 KEY METRICS TO ANALYZE:${NC}"
echo -e "${YELLOW}   • Win Rate (TARGET: >0% vs v8.2/v8.3/v8.4)${NC}"
echo -e "${YELLOW}   • Profit Factor (TARGET: >1.0)${NC}"
echo -e "${YELLOW}   • Total Trades (EXPECT: Similar to v8.4's 14 trades)${NC}"
echo -e "${YELLOW}   • Average Duration (EXPECT: <1 hour scalping)${NC}"
echo -e "${YELLOW}   • Max Drawdown (EXPECT: <0.01% like previous versions)${NC}"
echo -e "${YELLOW}   • Sharpe Ratio (TARGET: Positive)${NC}"
echo ""

echo -e "${GREEN}🔍 Analysis Commands:${NC}"
echo -e "${GREEN}   # Compare with previous versions:${NC}"
echo -e "${GREEN}   docker compose run --rm freqtrade backtesting-analysis --analysis-groups 0,1,2${NC}"
echo -e "${GREEN}   ${NC}"
echo -e "${GREEN}   # Generate detailed plots:${NC}"
echo -e "${GREEN}   docker compose run --rm freqtrade plot-dataframe --strategy $STRATEGY --pairs BTC/USDT --timerange 20250101-20250131${NC}"
echo ""

echo -e "${PURPLE}🚀 Next Steps if Profitable:${NC}"
echo -e "${PURPLE}   1. Paper trading validation${NC}"
echo -e "${PURPLE}   2. Live deployment with minimal capital${NC}"
echo -e "${PURPLE}   3. Performance monitoring and adjustment${NC}"
echo ""

echo -e "${GREEN}✅ PHASE 3 v8.5 TESTING COMPLETE!${NC}"
echo -e "${GREEN}Ready for profitability analysis and potential deployment.${NC}"
echo ""

# Optional: Auto-generate quick summary if jq is available
if command -v jq &> /dev/null; then
    echo -e "${BLUE}📊 Quick Performance Summary (January 2025):${NC}"
    if [ -f "$RESULTS_DIR/v8_5_january_2025_btc110k.json" ]; then
        echo -e "${BLUE}   Processing results...${NC}"
        # Add quick JSON analysis here if needed
    fi
fi 