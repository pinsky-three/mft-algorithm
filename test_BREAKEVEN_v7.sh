#!/bin/bash

echo "🏆 BREAKEVEN Test v7 - Final Push to Profitability"
echo "================================================="
echo "🎯 Baseline v6: 40.7% win rate, -1.58 USDT (68% mejor que v5)"
echo "💥 Target: Eliminar -1.58 USDT → Primera estrategia RENTABLE"
echo ""
echo "Micro-ajustes v7 BREAKEVEN:"
echo "📈 RSI: 55 → 60 (ultra selectivo, solo momentum fuerte)"
echo "💧 Volume: 1.7x → 2.0x (solo liquidez premium)"
echo "🎯 TP: 4.0x → 3.5x ATR (más conservador y alcanzable)"
echo "⚡ SL/Trailing: Sin cambios (2x/1.5x ATR funcionan)"
echo ""
echo "EXPECTATIVA: Primera estrategia RENTABLE de la serie 🚀"
echo ""

echo "🏆 Test v7 BREAKEVEN: Ultra-Selective Precision - Target >0 USDT"
docker compose run --rm freqtrade backtesting \
  -s MultiHorizonMomentum \
  -p BTC/USDT \
  --timerange 20241120-20241210 \
  --fee 0.0002 \
  --timeframe 1m

echo ""
echo "🎯 BREAKEVEN Targets v7:"
echo "   💰 Total profit: >0 USDT (BREAKTHROUGH HISTÓRICO)"
echo "   📈 Profit Factor: >1.0 (primera vez rentable)"
echo "   🎲 Win Rate: >42% (mantener calidad v6)"
echo "   📉 Fewer trades: Ultra selectivo, solo setups perfectos"
echo "   ⚡ Conservative TP: Más achievable, menos drawdown"
echo ""
echo "🚀 Si total profit >0 → DEPLOY INMEDIATO"
echo "🏆 HITO: Primer algoritmo rentable completado" 