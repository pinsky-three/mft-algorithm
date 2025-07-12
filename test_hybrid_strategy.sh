#!/bin/bash

echo "Testing CryptoScalpingHybrid - Best of Both Worlds"
echo "================================================="
echo "Hybrid Strategy Features:"
echo "✅ Video's key levels (15m narrative)"
echo "✅ Original momentum filters (EMA + RSI + MACD)"
echo "✅ 5m timeframe (balanced quality)"
echo "✅ 1:3 risk/reward ratio"
echo "✅ Crypto market adaptations"
echo ""

docker compose run --rm freqtrade backtesting \
  -s CryptoScalpingHybrid \
  -p BTC/USDT \
  --timerange 20250101-20250712 \
  --fee 0.0002 \
  --timeframe 5m \
  --export trades \
  --export-filename user_data/backtest_results/hybrid_strategy_results.json

echo ""
echo "=== PERFORMANCE COMPARISON ==="
echo "Original:      681 trades, 23.1% win rate, -1.53% return"
echo "Levels v1:    3423 trades, 84.6% win rate, -2.27% return"  
echo "Levels v2:    6026 trades, 76.9% win rate, -4.56% return"
echo "Hybrid:       Check results above!"
echo ""
echo "Target: 60-70% win rate, POSITIVE return, 1000-2000 trades" 