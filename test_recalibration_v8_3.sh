#!/bin/bash

# Test de Recalibración v8.3 - MultiHorizonMomentum Strategy
# Entrenamiento con datos 2024 completos + Validación en 2025

echo "======================================================================"
echo "🔄 RECALIBRACIÓN v8.3 - MultiHorizonMomentum Strategy"
echo "======================================================================"
echo ""
echo "🎯 OBJETIVO DE RECALIBRACIÓN:"
echo "   • Suavizar filtros ultra-selectivos v8.2 para mayor robustez"
echo "   • ADX threshold: 47 → 42 (menos restrictivo)"
echo "   • RSI long threshold: 63 → 58 (mayor captura de señales)" 
echo "   • RSI short threshold: 37 → 42 (balance simétrico)"
echo ""
echo "📊 PLAN DE PRUEBAS:"
echo "   1. Entrenar con datos 2024 COMPLETOS (calibración)"
echo "   2. Validar con datos Enero 2025 (test realista)"
echo "   3. Comparar v8.2 vs v8.3 en ambos períodos"
echo ""

# Test parameters
STRATEGY="MultiHorizonMomentum"
PAIRS="BTC/USDT"
TIMEFRAME="1m"
FEE="0.0002"  # 0.02% realistic fees

echo "=== FASE 1: ENTRENAMIENTO 2024 COMPLETO ==="
echo ""

# Define training periods for 2024
declare -a TRAIN_PERIODS=(
    "20240401-20240430:Abril-2024"
    "20240501-20240531:Mayo-2024"
    "20240601-20240630:Junio-2024"
    "20240701-20240731:Julio-2024"
    "20240801-20240831:Agosto-2024"
    "20240901-20240930:Septiembre-2024"
    "20241001-20241031:Octubre-2024"
    "20241101-20241130:Noviembre-2024"
    "20241201-20241231:Diciembre-2024"
    "20240401-20241231:TODO-2024"
)

# Create results directory
mkdir -p user_data/backtest_results/recalibration_v83_2024/

echo ">>> Entrenando estrategia v8.3 con períodos 2024..."
echo ""

for period_label in "${TRAIN_PERIODS[@]}"; do
    IFS=':' read -r dates label <<< "$period_label"
    
    echo ">>> Período de entrenamiento: $label ($dates)"
    echo "    Ejecutando backtest con fees realistas..."
    
    # Run backtest and save to specific file
    docker compose run --rm freqtrade backtesting \
        --strategy $STRATEGY \
        --pairs $PAIRS \
        --timeframe $TIMEFRAME \
        --fee $FEE \
        --timerange $dates \
        --cache=none \
        > "user_data/backtest_results/recalibration_v83_2024/${label}_training.log" 2>&1
    
    # Extract key metrics
    echo "    📈 Extrayendo métricas de entrenamiento..."
    grep -A 10 -E "BACKTESTING REPORT|Total profit|Avg Duration" \
        "user_data/backtest_results/recalibration_v83_2024/${label}_training.log" \
        > "user_data/backtest_results/recalibration_v83_2024/${label}_metrics.txt" 2>/dev/null || true
    
    echo "    ✅ Entrenamiento completado: $label"
    echo ""
done

echo "=== FASE 2: VALIDACIÓN 2025 ==="
echo ""

# Define validation periods for 2025
declare -a VALIDATION_PERIODS=(
    "20250101-20250107:Semana-1-2025"
    "20250108-20250113:Semana-2-2025"  
    "20250101-20250113:Enero-2025-Complete"
)

# Create validation results directory
mkdir -p user_data/backtest_results/recalibration_v83_2025/

echo ">>> Validando estrategia v8.3 recalibrada en 2025..."
echo ""

for period_label in "${VALIDATION_PERIODS[@]}"; do
    IFS=':' read -r dates label <<< "$period_label"
    
    echo ">>> Período de validación: $label ($dates)"
    echo "    Ejecutando validación con fees realistas..."
    
    # Run validation backtest
    docker compose run --rm freqtrade backtesting \
        --strategy $STRATEGY \
        --pairs $PAIRS \
        --timeframe $TIMEFRAME \
        --fee $FEE \
        --timerange $dates \
        --cache=none \
        > "user_data/backtest_results/recalibration_v83_2025/${label}_validation.log" 2>&1
    
    # Extract key metrics
    echo "    📈 Extrayendo métricas de validación..."
    grep -A 10 -E "BACKTESTING REPORT|Total profit|Avg Duration" \
        "user_data/backtest_results/recalibration_v83_2025/${label}_validation.log" \
        > "user_data/backtest_results/recalibration_v83_2025/${label}_metrics.txt" 2>/dev/null || true
    
    echo "    ✅ Validación completada: $label"
    echo ""
done

echo "=== RESUMEN DE RECALIBRACIÓN v8.3 ==="
echo ""
echo "📊 ENTRENAMIENTO 2024 - Métricas clave:"
echo ""

# Display training results
for period_label in "${TRAIN_PERIODS[@]}"; do
    IFS=':' read -r dates label <<< "$period_label"
    echo "📈 $label:"
    if [ -f "user_data/backtest_results/recalibration_v83_2024/${label}_metrics.txt" ]; then
        cat "user_data/backtest_results/recalibration_v83_2024/${label}_metrics.txt" | head -10
    else
        echo "    ❌ No hay métricas disponibles"
    fi
    echo ""
done

echo "📊 VALIDACIÓN 2025 - Métricas clave:"
echo ""

# Display validation results  
for period_label in "${VALIDATION_PERIODS[@]}"; do
    IFS=':' read -r dates label <<< "$period_label"
    echo "📈 $label:"
    if [ -f "user_data/backtest_results/recalibration_v83_2025/${label}_metrics.txt" ]; then
        cat "user_data/backtest_results/recalibration_v83_2025/${label}_metrics.txt" | head -10
    else
        echo "    ❌ No hay métricas disponibles"
    fi
    echo ""
done

echo "=== COMPARACIÓN v8.2 vs v8.3 ==="
echo ""
echo "🔍 PUNTOS CLAVE A ANALIZAR:"
echo "   • ¿Aumentó la frecuencia de trading en 2025? (objetivo: >0.5 trades/día)"
echo "   • ¿Mejoró el win rate? (objetivo: >20% en 2025)"
echo "   • ¿Se mantiene el control de riesgo? (drawdown <0.2%)"
echo "   • ¿Duración promedio sigue siendo <30min?"
echo "   • ¿Balance entre selectividad y robustez optimizado?"
echo ""

echo "📁 Todos los resultados guardados en:"
echo "   • Entrenamiento 2024: user_data/backtest_results/recalibration_v83_2024/"
echo "   • Validación 2025: user_data/backtest_results/recalibration_v83_2025/"
echo ""

echo "======================================================================"
echo "🎯 RECALIBRACIÓN v8.3 COMPLETADA"
echo "======================================================================"
echo ""
echo "📋 PRÓXIMOS PASOS:"
echo "   1. Analizar métricas de entrenamiento 2024"
echo "   2. Comparar performance 2025: v8.2 vs v8.3"
echo "   3. Ajustar parámetros si es necesario"
echo "   4. Implementar en trading real si validación exitosa" 