#!/bin/bash

echo "🔧 Testing v2.1 balanced adjustments..."
echo "======================================="
echo "Ajustes más conservadores v2.1:"
echo "📉 SL: 0.8x → 1.2x ATR (más realista)"
echo "📈 TP: 4.0x → 3.0x ATR (más alcanzable)" 
echo "📊 Volume: 2.0x → 1.7x (menos restrictivo)"
echo "⚡ Fast exit: >0.5 → >0.8 ATR (solo reversiones fuertes)"
echo ""

echo "📊 Test v2.1: Con fees reales Binance (0.04%)"
docker compose run --rm freqtrade backtesting \
  -s MultiHorizonMomentum \
  -p BTC/USDT \
  --timerange 20241201-20241202 \
  --fee 0.0004 \
  --timeframe 1m

echo ""
echo "🎯 Objetivo v2.1:"
echo "   🎲 Win Rate: Recuperar >30% (vs. v2 0%)"
echo "   ⏱️  Duration: Mantener <20min"
echo "   💰 Avg profit: Target >-0.05% (vs. v2 -0.13%)"
echo "   📈 Profit Factor: Target >0.5 (vs. v2 0.00)" 