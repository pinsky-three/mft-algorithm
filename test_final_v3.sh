#!/bin/bash

echo "🚀 Final Test v3 - Market Noise Resistant"
echo "==========================================="
echo "Solución final al problema de fees + market noise:"
echo "💪 SL: 1.2x → 2.0x ATR (margen realista para noise)"
echo "🎯 TP: 3.0x → 4.0x ATR (R:R 1:2 óptimo)" 
echo "📊 Fees: Maker 0.02% (vs. Taker 0.04%)"
echo "⚡ Filtros: Direccional 15m + Volume 1.7x + Fast exit"
echo ""

echo "📊 Test Final: Con maker fees (0.02%)"
docker compose run --rm freqtrade backtesting \
  -s MultiHorizonMomentum \
  -p BTC/USDT \
  --timerange 20241120-20241210 \
  --fee 0.0002 \
  --timeframe 1m

echo ""
echo "🎯 Objetivo Final v3:"
echo "   🎲 Win Rate: >20% (vs. todas las versiones anteriores 0%)"
echo "   ⏱️  Duration: Mantener ~15min (óptimo para scalping)"
echo "   💰 Avg profit: >0% (break-even mínimo)"
echo "   📈 Profit Factor: >1.0 (rentable por primera vez)"
echo ""
echo "💡 Si funciona → usar limit orders como maker en producción"
echo "🔧 Si no funciona → problema fundamental en la señal, no en exits" 