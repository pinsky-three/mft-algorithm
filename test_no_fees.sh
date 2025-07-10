#!/bin/bash

echo "🧪 Testing strategy v2 optimizations..."
echo "======================================="
echo "Cambios implementados:"
echo "✅ SL: 1.0x → 0.8x ATR"
echo "✅ TP: 3.0x → 4.0x ATR" 
echo "✅ Volume filter: 1.5x → 2.0x"
echo "✅ Fast exit: Vela roja >0.5 ATR"
echo ""

# Test 1: Sin fees (validación de edge)
echo "📊 Test 1: Sin fees (edge validation)"
docker compose run --rm freqtrade backtesting \
  -s MultiHorizonMomentum \
  -p BTC/USDT \
  --timerange 20241201-20241202 \
  --fee 0 \
  --timeframe 1m

echo ""
echo "📊 Test 2: Con fees reales Binance (0.04%)"
docker compose run --rm freqtrade backtesting \
  -s MultiHorizonMomentum \
  -p BTC/USDT \
  --timerange 20241201-20241202 \
  --fee 0.0004 \
  --timeframe 1m

echo ""
echo "🎯 Métricas objetivo v2:"
echo "   📈 Profit Factor sin fees: >1.2 (vs. anterior 0.15)"
echo "   🎲 Win Rate: 40-60% (mantener)"
echo "   ⏱️  Avg trade duration: <30min (vs. anterior >1h)"
echo "   💰 Avg profit: >0.15% (vs. anterior -0.08%)" 