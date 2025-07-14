#!/bin/bash
docker compose run \
    --rm freqtrade backtesting \
    -s CryptoScalpingOptimized \
    -p BTC/USDT ETH/USDT SOL/USDT \
    --timerange 20250101-20250701 \
    --fee 0.0002 \
    --timeframe 1m \
    --export trades