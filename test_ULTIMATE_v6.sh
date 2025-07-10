#!/bin/bash

echo "🚀 ULTIMATE Test v6 - Pure ATR Strategy"
echo "======================================="
echo "💥 BREAKTHROUGH DISCOVERY: ALL exit signals toxic in 1m"
echo "📊 v5 Analysis: Custom exit 47.2% win rate vs Exit signals 0%"
echo "✅ Solution: 100% ATR-based exits, ZERO exit signals"
echo ""
echo "v6 ULTIMATE Changes:"
echo "🎯 Entries: Triple EMA + RSI>55 + MACD bullish (proven precise)"
echo "🚫 Exit signals: COMPLETAMENTE eliminados (EMA, RSI, MACD = 0% win rate)"
echo "⚡ Pure ATR: TP 4x, SL 2x, Trailing 1.5x (47.2% win rate)"
echo "💰 Expected: PRIMERA ESTRATEGIA RENTABLE 🏆"
echo ""

echo "🏆 Test v6 ULTIMATE: Pure ATR Strategy - Expected PROFITABLE"
docker compose run --rm freqtrade backtesting \
  -s MultiHorizonMomentum \
  -p BTC/USDT \
  --timerange 20241120-20241210 \
  --fee 0.0002 \
  --timeframe 1m

echo ""
echo "🎯 ULTIMATE Expectations v6:"
echo "   💰 Profit Factor: >1.0 (PRIMERA VEZ RENTABLE)"
echo "   📈 Total profit: >0 USDT (BREAKTHROUGH)"
echo "   🎲 Win Rate: >45% (solo custom exits)"
echo "   ⚡ Exit reason: 100% custom_exit"
echo "   🏆 Profit Factor esperado: 1.2-1.5"
echo ""
echo "🚀 Si PF >1.0 → DEPLOY INMEDIATO EN PRODUCCIÓN"
echo "🎯 Target: Primer algoritmo rentable de la serie" 