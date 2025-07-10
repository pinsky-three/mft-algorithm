#!/bin/bash

# Test script for MultiHorizonMomentum Strategy v8.2 - SCALPER OPTIMIZED
# Ultra-fast scalping with refined filters and optimized ATR targets

echo "===================================================================="
echo "Testing MultiHorizonMomentum Strategy v8.2 - SCALPER OPTIMIZED"
echo "===================================================================="
echo ""
echo "🎯 SCALPING OPTIMIZATIONS v8.2:"
echo "   • ADX threshold: 50 → 47 (balanced precision/robustness)"
echo "   • RSI long threshold: 65 → 63 (refined selectivity)"  
echo "   • RSI short threshold: 35 → 37 (refined selectivity)"
echo "   • ATR Take Profit: 3.5x → 2.5x (faster profit taking)"
echo "   • ATR Stop Loss: 2.0x → 1.5x (tighter risk control)"
echo "   • ATR Trailing: 1.5x → 1.2x (aggressive profit protection)"
echo ""
echo "📊 SCALPING TARGETS:"
echo "   • Average trade duration: <30 minutes"
echo "   • Win rate target: 30%+ consistent"
echo "   • Risk/Reward optimized for quick moves"
echo "   • Minimal slippage and faster exits"
echo ""

# Test parameters optimized for scalping analysis
STRATEGY="MultiHorizonMomentum"
PAIRS="BTC/USDT"
TIMEFRAME="1m"
FEE="0.0002"  # 0.02% realistic fees

echo "Strategy: $STRATEGY v8.2 SCALPER"
echo "Pairs: $PAIRS"
echo "Timeframe: $TIMEFRAME (optimal for scalping)"
echo "Fees: $FEE%"
echo ""

# Test 1: High volatility period (good for scalping)
echo "============================================"
echo "🚀 TEST 1: Aug 2024 - Scalping Performance"
echo "============================================"
START_DATE="20240801"
END_DATE="20240831"

echo ">>> Testing scalping in August 2024..."
echo ">>> Expected: Better balance of trades vs win rate"

RESULT1=$(docker compose run --rm freqtrade backtesting \
    --strategy $STRATEGY \
    --pairs $PAIRS \
    --timeframe $TIMEFRAME \
    --fee $FEE \
    --timerange $START_DATE-$END_DATE \
    --cache=none | tee /tmp/scalper_aug.log)

# Extract key metrics for scalping analysis
TRADES_AUG=$(echo "$RESULT1" | grep -E "Total/Daily Avg Trades" | grep -oE "[0-9]+" | head -1)
WINRATE_AUG=$(echo "$RESULT1" | grep -oE "Win%" | tail -1)
DURATION_AUG=$(echo "$RESULT1" | grep -E "Avg Duration" | grep -oE "[0-9]+:[0-9]+" | head -1)

echo ""
echo "📊 August Scalping Metrics:"
echo "   • Trades: $TRADES_AUG"
echo "   • Average Duration: $DURATION_AUG (Target: <30min)"
echo "   • Performance: Check above results"
echo ""

# Test 2: Different market conditions
echo "============================================"
echo "🎯 TEST 2: Sep 2024 - Consistency Check"
echo "============================================"
START_DATE="20240901"
END_DATE="20240930"

echo ">>> Testing scalping consistency in September..."

RESULT2=$(docker compose run --rm freqtrade backtesting \
    --strategy $STRATEGY \
    --pairs $PAIRS \
    --timeframe $TIMEFRAME \
    --fee $FEE \
    --timerange $START_DATE-$END_DATE \
    --cache=none | tee /tmp/scalper_sep.log)

echo ""

# Test 3: Recent period validation
echo "============================================"
echo "⚡ TEST 3: Oct-Dec 2024 - Recent Validation"
echo "============================================"
START_DATE="20241001"
END_DATE="20241210"

echo ">>> Testing scalping in recent market conditions..."

RESULT3=$(docker compose run --rm freqtrade backtesting \
    --strategy $STRATEGY \
    --pairs $PAIRS \
    --timeframe $TIMEFRAME \
    --fee $FEE \
    --timerange $START_DATE-$END_DATE \
    --cache=none | tee /tmp/scalper_recent.log)

echo ""
echo "============================================"
echo "📈 SCALPING ANALYSIS SUMMARY"
echo "============================================"
echo ""
echo "🔄 COMPARISON WITH PREVIOUS VERSIONS:"
echo ""
echo "📊 v8.0 Baseline Results:"
echo "   • Aug: 34 trades, 23.5% win rate, ~1h duration"
echo "   • Sep: 22 trades, 18.2% win rate, ~1h duration"  
echo "   • Oct-Dec: 111 trades, 23.4% win rate, ~1h duration"
echo ""
echo "🎯 v8.1 Ultra-Selective Results:"
echo "   • Aug: 11 trades, 18.2% win rate, ~47min duration"
echo "   • Sep: 3 trades, 33.3% win rate, ~6min duration"
echo "   • Oct-Dec: 22 trades, 13.6% win rate, ~15min duration"
echo ""
echo "⚡ v8.2 SCALPER Results: (See above)"
echo ""
echo "🎯 SCALPING SUCCESS CRITERIA:"
echo "   ✅ Average duration <30 minutes"
echo "   ✅ Win rate >25% consistently"
echo "   ✅ Positive P&L with realistic fees"
echo "   ✅ Improved trade frequency vs v8.1"
echo "   ✅ Better balance precision/robustness"
echo ""
echo "🚀 NEXT STEPS IF SUCCESSFUL:"
echo "   • Fine-tune volume filters for scalping"
echo "   • Add price action confirmation"
echo "   • Test on additional pairs"
echo "   • Implement dynamic ATR scaling"
echo ""
echo "⚠️  SCALPING RISK REMINDERS:"
echo "   • Higher frequency = more fee impact"
echo "   • Requires stable low-latency connection"
echo "   • Market microstructure matters"
echo "   • Optimal during high volume periods" 