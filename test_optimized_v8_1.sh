#!/bin/bash

# Test script for MultiHorizonMomentum Strategy v8.1 - OPTIMIZED (Phase 1)
# Enhanced strategy with ultra-selective filters for higher win rate

echo "===================================================================="
echo "Testing MultiHorizonMomentum Strategy v8.1 - OPTIMIZED (Phase 1)"
echo "===================================================================="
echo ""
echo "🎯 OPTIMIZATIONS IMPLEMENTED:"
echo "   • ADX threshold: 40 → 50 (ultra-strong trends only)"
echo "   • RSI long threshold: 60 → 65 (extreme bullish momentum)"  
echo "   • RSI short threshold: 40 → 35 (extreme bearish momentum)"
echo "   • Volume filter: 2.0x → 3.0x (premium liquidity only)"
echo ""
echo "📊 EXPECTED IMPROVEMENTS:"
echo "   • ~50% fewer trades (higher selectivity)"
echo "   • Win rate: 23% → 35%+ target"
echo "   • Better fee efficiency"
echo ""

# Test parameters
STRATEGY="MultiHorizonMomentum"
PAIRS="BTC/USDT"
TIMEFRAME="1m"
FEE="0.0002"  # 0.02% realistic fees

echo "Strategy: $STRATEGY v8.1"
echo "Pairs: $PAIRS"
echo "Timeframe: $TIMEFRAME"
echo "Fees: $FEE%"
echo ""

# Test 1: August 2024 (baseline comparison)
echo "============================================"
echo "🧪 TEST 1: August 2024 (Baseline Period)"
echo "============================================"
START_DATE="20240801"
END_DATE="20240831"

echo ">>> Testing period: $START_DATE to $END_DATE"
echo ">>> Running v8.1 optimized backtest..."

docker compose run --rm freqtrade backtesting \
    --strategy $STRATEGY \
    --pairs $PAIRS \
    --timeframe $TIMEFRAME \
    --fee $FEE \
    --timerange $START_DATE-$END_DATE \
    --cache=none

echo ""
echo "============================================"
echo "🧪 TEST 2: September 2024 (Validation)"
echo "============================================"

# Test 2: September 2024 (validation)
START_DATE="20240901"
END_DATE="20240930"

echo ">>> Testing period: $START_DATE to $END_DATE"
echo ">>> Running v8.1 optimized backtest..."

docker compose run --rm freqtrade backtesting \
    --strategy $STRATEGY \
    --pairs $PAIRS \
    --timeframe $TIMEFRAME \
    --fee $FEE \
    --timerange $START_DATE-$END_DATE \
    --cache=none

echo ""
echo "============================================"
echo "🧪 TEST 3: Oct-Dec 2024 (Recent Period)"
echo "============================================"

# Test 3: Oct-Dec 2024 (recent period)
START_DATE="20241001"
END_DATE="20241210"

echo ">>> Testing period: $START_DATE to $END_DATE"
echo ">>> Running v8.1 optimized backtest..."

docker compose run --rm freqtrade backtesting \
    --strategy $STRATEGY \
    --pairs $PAIRS \
    --timeframe $TIMEFRAME \
    --fee $FEE \
    --timerange $START_DATE-$END_DATE \
    --cache=none

echo ""
echo "============================================"
echo "📋 COMPARISON ANALYSIS"
echo "============================================"
echo ""
echo "📊 BASELINE RESULTS (v8.0):"
echo "   • Aug 2024: 34 trades, 23.5% win rate, -0.02% P&L"
echo "   • Sep 2024: 22 trades, 18.2% win rate, -0.10% P&L"
echo "   • Oct-Dec: 111 trades, 23.4% win rate, -0.14% P&L"
echo ""
echo "🎯 EXPECTED v8.1 IMPROVEMENTS:"
echo "   • 50% fewer trades per period"
echo "   • 35%+ win rate target"
echo "   • Positive P&L with realistic fees"
echo ""
echo "✅ Analysis complete! Compare results above with baseline." 