#!/bin/bash

# Test script for MultiHorizonMomentum Strategy v8 - TEMA Extended
# Enhanced strategy combining original EMA momentum with TEMA trend-following

echo "==================================================================="
echo "Testing MultiHorizonMomentum Strategy v8 - TEMA Extended"
echo "==================================================================="
echo ""

# Test parameters
STRATEGY="MultiHorizonMomentum"
PAIRS="BTC/USDT"
TIMEFRAME="1m"
FEE="0.0002"  # 0.1% realistic fees
START_DATE="20241001"
END_DATE="20241210"

echo "Strategy: $STRATEGY"
echo "Pairs: $PAIRS"
echo "Timeframe: $TIMEFRAME"
echo "Fees: $FEE%"
echo "Period: $START_DATE to $END_DATE"
echo ""

echo ">>> Running backtest with realistic fees..."
docker compose run --rm freqtrade backtesting \
    --strategy $STRATEGY \
    --pairs $PAIRS \
    --timeframe $TIMEFRAME \
    --fee $FEE \
    --timerange $START_DATE-$END_DATE \
    --export trades \
    --export-filename user_data/backtest_results/tema_extended_v8_with_fees.json

echo ""
echo ">>> Running backtest without fees (edge validation)..."
docker compose run --rm freqtrade backtesting \
    --strategy $STRATEGY \
    --pairs $PAIRS \
    --timeframe $TIMEFRAME \
    --fee 0 \
    --timerange $START_DATE-$END_DATE \
    --export trades \
    --export-filename user_data/backtest_results/tema_extended_v8_no_fees.json

echo ""
echo "==================================================================="
echo "TEMA Extended v8 Features Tested:"
echo "==================================================================="
echo "✓ Original Triple EMA alignment (30/120/360)"
echo "✓ TEMA short-term crossover (10/80)"  
echo "✓ TEMA long-term trend (4h: 20/70)"
echo "✓ ADX momentum filter (>40)"
echo "✓ CMO directional momentum (>40 long, <-40 short)"
echo "✓ Volume surge filter (2x average)"
echo "✓ 15m directional filter"
echo "✓ ATR-based risk management (2x SL, 3.5x TP, 1.5x Trail)"
echo "✓ Support for both LONG and SHORT trades (if enabled)"
echo ""
echo "Backtest completed! Check results in user_data/backtest_results/" 