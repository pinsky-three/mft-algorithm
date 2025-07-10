#!/bin/bash

echo "🧪 Testing strategy without fees to validate edge..."
echo "===================================================="

# Test 1: Sin fees (24h)
echo "📊 Test 1: Sin fees (24 horas)"
docker compose run --rm freqtrade backtesting \
  -s MultiHorizonMomentum \
  -p BTC/USDT \
  --timerange 20241201-20241202 \
  --fee 0 \
  --timeframe 1m \


echo ""
echo "📊 Test 2: Con fees reales (24 horas)"
docker compose run --rm freqtrade backtesting \
  -s MultiHorizonMomentum \
  -p BTC/USDT \
  --timerange 20241201-20241202 \
  --fee 0.1 \
  --timeframe 1m \


echo ""
echo "💡 Comparar Profit Factor:"
echo "   - Sin fees PF > 1.1-1.2 → sistema tiene edge, solo necesita cubrir fricción"
echo "   - Sin fees PF ≈ 1.0 → falta señal, necesita mejor filtro" 