#!/bin/bash

echo "🚀 PHASE 3 FINAL TEST - Market Regime Mastery"
echo "============================================="
echo "Testing Phase 3 Final with smart regime detection to address monthly consistency"
echo ""

echo "🔄 Testing Phase 3 Final strategy for January 2025..."
echo "Strategy: CryptoScalpingPhase3Final (regime-aware)"
echo "Timerange: 20250101-20250201"
echo "Pairs: BTC/USDT ETH/USDT SOL/USDT"
echo ""

echo "📊 REGIME DETECTION IMPROVEMENTS:"
echo "   • Trend Regime: Multi-timeframe trend alignment"
echo "   • Volatility Regime: ATR percentile + expansion analysis"  
echo "   • Momentum Regime: Quality momentum with directional strength"
echo "   • Choppiness Regime: Avoid ranging/choppy markets"
echo "   • Performance Gating: Stop trading if win rate < 72%"
echo "   • Adaptive Frequency: Reduce trading during poor performance"
echo ""

echo "🎯 TARGET vs PHASE 3 PRACTICAL:"
echo "   • Monthly Consistency: 3/6 positive → 5/6 positive months"
echo "   • Win Rate Floor: 62-68% → 75%+ minimum"
echo "   • Total Profit: +3.647 USDT → +6-8 USDT target"
echo ""

echo "🚀 Starting backtest..."

# Run the backtest
docker compose run --rm freqtrade backtesting \
  -s CryptoScalpingPhase3Final \
  -p BTC/USDT ETH/USDT SOL/USDT \
  --timerange 20250101-20250201 \
  --fee 0.0002 \
  --timeframe 1m

echo ""
echo "✅ Phase 3 Final test completed!" 