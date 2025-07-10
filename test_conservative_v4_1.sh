#!/bin/bash

echo "🛡️  Conservative Test v4.1 - Exit Signal Fix"
echo "============================================="
echo "Ajustes conservadores desde v4 22.2% win rate:"
echo "📈 RSI entrada: 50 → 55 (más selectivo)"
echo "📉 RSI salida: 45 → 35 (menos agresivo)"
echo "📊 MACD salida: Cruce → 5% por debajo (confirma bearish)"
echo "💧 Exit con volumen: Solo si volumen cae 10%+"
echo "⚡ Exit lógica: Combinar señales para reducir false signals"
echo ""
echo "Objetivo: Resolver exit signals 0% win rate → >15%"
echo "Mantener custom exit 42.1% win rate"
echo ""

echo "📊 Test v4.1: Período extendido (20 días) - Conservative exits"
docker compose run --rm freqtrade backtesting \
  -s MultiHorizonMomentum \
  -p BTC/USDT \
  --timerange 20241120-20241210 \
  --fee 0.0002 \
  --timeframe 1m

echo ""
echo "📈 Comparación v4 → v4.1:"
echo "   🎯 Win Rate: Mantener >20% (era 22.2%)"
echo "   📈 Exit signals win rate: >15% (era 0%)"
echo "   📉 Exit signals trades: Reducir cantidad"
echo "   💰 Profit Factor: >0.5 (era 0.11)"
echo "   ⚡ Custom exit: Mantener 42.1%"
echo ""
echo "🎯 Si exit signals >15% win rate → Gran éxito"
echo "🔧 Si sigue 0% → Eliminar exit signals completamente" 