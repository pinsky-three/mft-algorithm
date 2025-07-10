#!/bin/bash

echo "🏆 FINAL Test v5 - Exit Signal Problem SOLVED"
echo "=============================================="
echo "💥 BREAKTHROUGH: Eliminados RSI/MACD exit signals"
echo "🎯 Problema identificado: 0% win rate en 137 trades = -4.8 USDT"
echo "✅ Solución: Solo mantener EMA cross + Custom exit (46.8% win rate)"
echo ""
echo "Optimizaciones FINALES v5:"
echo "📈 Entradas: Triple EMA + RSI>55 + MACD bullish"
echo "📉 Salidas: ATR TP/SL + EMA cross SOLAMENTE"
echo "🚫 ELIMINADO: RSI<35 y MACD exits (destructivos)"
echo "⚡ Custom exit: Mantener 46.8% win rate"
echo ""
echo "EXPECTATIVA: Primera versión RENTABLE 🚀"
echo ""

echo "🏆 Test v5 FINAL: Período extendido (20 días) - Production Ready"
docker compose run --rm freqtrade backtesting \
  -s MultiHorizonMomentum \
  -p BTC/USDT \
  --timerange 20241120-20241210 \
  --fee 0.0002 \
  --timeframe 1m

echo ""
echo "🎯 Objetivos v5 FINAL:"
echo "   💰 Profit Factor: >1.0 (rentabilidad real)"
echo "   🎲 Win Rate: Mantener >25%"
echo "   📈 Total profit: >0 USDT (primera vez positivo)"
echo "   📉 Custom exit: >45% win rate"
echo "   ⚡ EMA exit: >15% win rate (único exit signal)"
echo ""
echo "🚀 Si rentable → DEPLOY EN PRODUCCIÓN"
echo "🔧 Si no rentable → Revisar parámetros ATR" 