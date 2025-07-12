#!/bin/bash

docker compose run --rm freqtrade backtesting \
  -s MultiHorizonMomentum \
  -p BTC/USDT \
  --timerange 20250101-20250712 \
  --fee 0.0002 \
  --timeframe 1m