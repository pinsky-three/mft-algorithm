#!/bin/bash

echo "📊 MULTI-PAIR DATA DOWNLOAD - BTC, ETH, SOL"
echo "============================================="
echo ""
echo "🎯 Target: Download 1m, 5m, 15m data for comprehensive testing"
echo "📈 Pairs: BTC/USDT, ETH/USDT, SOL/USDT"
echo "⏰ Timeframes: 1m, 5m, 15m"
echo ""

# Date range for comprehensive data
START_DATE="20240101"
END_DATE="20250715"

echo "📅 Date Range: ${START_DATE} to ${END_DATE}"
echo ""

# Check existing data
echo "🔍 EXISTING DATA CHECK:"
echo "======================="
ls -la user_data/data/binance/ | grep -E "(BTC|ETH|SOL)_USDT" | awk '{print $9, $5}'
echo ""

# Download missing data
echo "⬇️  DOWNLOADING MISSING DATA:"
echo "============================"

# ETH/USDT - Missing 15m
echo "📈 Downloading ETH/USDT 15m data..."
docker compose run --rm freqtrade download-data \
  --exchange binance \
  --pairs ETH/USDT \
  --timeframes 15m \
  --timerange ${START_DATE}-${END_DATE} \
  --data-format-ohlcv json

echo ""
echo "🔄 ETH/USDT 15m download complete!"
echo ""

# SOL/USDT - Missing all timeframes
echo "🌟 Downloading SOL/USDT 1m data..."
docker compose run --rm freqtrade download-data \
  --exchange binance \
  --pairs SOL/USDT \
  --timeframes 1m \
  --timerange ${START_DATE}-${END_DATE} \
  --data-format-ohlcv json

echo ""
echo "🌟 Downloading SOL/USDT 5m data..."
docker compose run --rm freqtrade download-data \
  --exchange binance \
  --pairs SOL/USDT \
  --timeframes 5m \
  --timerange ${START_DATE}-${END_DATE} \
  --data-format-ohlcv json

echo ""
echo "🌟 Downloading SOL/USDT 15m data..."
docker compose run --rm freqtrade download-data \
  --exchange binance \
  --pairs SOL/USDT \
  --timeframes 15m \
  --timerange ${START_DATE}-${END_DATE} \
  --data-format-ohlcv json

echo ""
echo "✅ SOL/USDT all timeframes download complete!"
echo ""

# Final data check
echo "🏆 FINAL DATA INVENTORY:"
echo "========================"
echo "📊 Available pairs and timeframes:"
ls -la user_data/data/binance/ | grep -E "(BTC|ETH|SOL)_USDT-(1m|5m|15m)" | awk '{print $9, $5}' | sort
echo ""

echo "🎯 MULTI-PAIR DATA DOWNLOAD COMPLETE!"
echo ""
echo "📈 Ready for comprehensive testing:"
echo "   ✅ BTC/USDT: 1m, 5m, 15m"
echo "   ✅ ETH/USDT: 1m, 5m, 15m"  
echo "   ✅ SOL/USDT: 1m, 5m, 15m"
echo ""
echo "🚀 NEXT STEPS:"
echo "   1. Test current ROI-only strategy on all pairs"
echo "   2. Compare performance across timeframes"
echo "   3. Optimize for 3% monthly target with multiple pairs"
echo "   4. Validate multi-pair trading opportunities" 