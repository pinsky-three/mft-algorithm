#!/bin/bash

echo "🎯 Precision Test v4 - Advanced Momentum Filters"
echo "================================================="
echo "Nuevos filtros implementados v4:"
echo "📈 RSI: >50 (momentum alcista)"
echo "📊 MACD: Por encima de señal (tendencia fuerte)"
echo "💧 Volume ROC: Creciente últimos 5min (liquidez dinámica)"
echo "⚡ Multi-exit: EMA + RSI<45 + MACD bearish + red candle"
echo ""
echo "Objetivo: Aumentar win rate 4.8% → 25-35%"
echo "Expectativa: Menos trades pero más precisos"
echo ""

echo "📊 Test v4: Período extendido (20 días) con maker fees"
docker compose run --rm freqtrade backtesting \
  -s MultiHorizonMomentum \
  -p BTC/USDT \
  --timerange 20241120-20241210 \
  --fee 0.0002 \
  --timeframe 1m

echo ""
echo "🎯 Objetivos v4:"
echo "   🎲 Win Rate: 25-35% (vs. v3 4.8%)"
echo "   📉 Trades totales: Menos cantidad, más calidad"
echo "   💰 Avg profit: >0.1% (trades más decisivos)"
echo "   📈 Profit Factor: >1.2 (rentabilidad clara)"
echo "   ⏱️  Duration: 15-30min (balance óptimo)"
echo ""
echo "💡 Si win rate >30% → Deploy en producción"
echo "🔧 Si win rate 15-25% → Ajustar thresholds (RSI 55, MACD más estricto)" 