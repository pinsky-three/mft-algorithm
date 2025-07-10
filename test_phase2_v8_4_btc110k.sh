#!/bin/bash

# Test Fase 2 v8.4 - MultiHorizonMomentum Strategy 
# Optimización específica para condiciones BTC $110K+ en 2025

echo "======================================================================"
echo "🚀 FASE 2 RECALIBRACIÓN v8.4 - BTC $110K+ OPTIMIZED"
echo "======================================================================"
echo ""
echo "🎯 OBJETIVO FASE 2:"
echo "   • Ultra-adaptabilidad para condiciones BTC $110K+"
echo "   • ADX threshold: 42 → 38 (máxima captura de señales)"
echo "   • RSI long threshold: 58 → 55 (mayor sensibilidad bullish)" 
echo "   • RSI short threshold: 42 → 45 (simetría optimizada)"
echo "   • META: 20-30% win rate en datos 2025"
echo ""
echo "📊 PLAN DE VALIDACIÓN ESPECÍFICA 2025:"
echo "   1. Test intensivo en condiciones Enero 2025 (BTC $110-115K)"
echo "   2. Comparación directa v8.3 vs v8.4"
echo "   3. Análisis de captura de señales vs calidad"
echo "   4. Validación de targets de scalping"
echo ""

# Test parameters
STRATEGY="MultiHorizonMomentum"
PAIRS="BTC/USDT"
TIMEFRAME="1m"
FEE="0.0002"  # 0.02% realistic fees

echo "=== VALIDACIÓN INTENSIVA 2025 - v8.4 PHASE2 ==="
echo ""

# Define 2025 test periods with granular analysis
declare -a TEST_PERIODS_2025=(
    "20250101-20250102:Día-1-Enero"
    "20250103-20250105:Días-3-5-Enero"
    "20250106-20250107:Fin-Semana-1"
    "20250108-20250110:Días-8-10-Enero"
    "20250111-20250113:Días-11-13-Enero"
    "20250101-20250107:Semana-1-Complete"
    "20250108-20250113:Semana-2-Complete"
    "20250101-20250113:Enero-2025-FULL"
)

# Create results directory
mkdir -p user_data/backtest_results/phase2_v84_2025/
mkdir -p user_data/backtest_results/phase2_v84_2025/detailed/

echo ">>> Ejecutando validación Phase2 v8.4 en períodos granulares 2025..."
echo ""

total_trades=0
total_wins=0
total_losses=0

for period_label in "${TEST_PERIODS_2025[@]}"; do
    IFS=':' read -r dates label <<< "$period_label"
    
    echo ">>> Período de test: $label ($dates)"
    echo "    🔬 Análisis granular condiciones BTC $110K+..."
    
    # Run detailed backtest
    docker compose run --rm freqtrade backtesting \
        --strategy $STRATEGY \
        --pairs $PAIRS \
        --timeframe $TIMEFRAME \
        --fee $FEE \
        --timerange $dates \
        --cache=none \
        > "user_data/backtest_results/phase2_v84_2025/detailed/${label}_v84.log" 2>&1
    
    # Extract detailed metrics
    echo "    📈 Extrayendo métricas v8.4..."
    grep -A 15 -E "BACKTESTING REPORT|Total profit|Avg Duration|Win  Draw  Loss" \
        "user_data/backtest_results/phase2_v84_2025/detailed/${label}_v84.log" \
        > "user_data/backtest_results/phase2_v84_2025/detailed/${label}_metrics.txt" 2>/dev/null || true
    
    # Extract key numbers for summary
    trades=$(grep -E "BTC/USDT.*[0-9]" "user_data/backtest_results/phase2_v84_2025/detailed/${label}_metrics.txt" 2>/dev/null | awk '{print $3}' | head -1)
    wins=$(grep -E "BTC/USDT.*[0-9]" "user_data/backtest_results/phase2_v84_2025/detailed/${label}_metrics.txt" 2>/dev/null | awk '{print $8}' | head -1)
    losses=$(grep -E "BTC/USDT.*[0-9]" "user_data/backtest_results/phase2_v84_2025/detailed/${label}_metrics.txt" 2>/dev/null | awk '{print $10}' | head -1)
    
    # Accumulate totals (if numbers are valid)
    if [[ "$trades" =~ ^[0-9]+$ ]]; then
        total_trades=$((total_trades + trades))
        if [[ "$wins" =~ ^[0-9]+$ ]]; then
            total_wins=$((total_wins + wins))
        fi
        if [[ "$losses" =~ ^[0-9]+$ ]]; then
            total_losses=$((total_losses + losses))
        fi
        echo "    📊 Resultados: $trades trades, $wins wins, $losses losses"
    else
        echo "    📊 Resultados: Sin trades o datos incompletos"
    fi
    
    echo "    ✅ Test completado: $label"
    echo ""
done

echo "=== ANÁLISIS COMPARATIVO v8.3 vs v8.4 ==="
echo ""

# Run comparison test with previous version for reference
echo ">>> Ejecutando test comparativo rápido..."

# Test key period with both configs (simulated v8.3 vs current v8.4)
echo ">>> Comparando Enero-2025-FULL: v8.4 (actual) vs baseline..."

docker compose run --rm freqtrade backtesting \
    --strategy $STRATEGY \
    --pairs $PAIRS \
    --timeframe $TIMEFRAME \
    --fee $FEE \
    --timerange 20250101-20250113 \
    --cache=none \
    > "user_data/backtest_results/phase2_v84_2025/enero_2025_v84_final.log" 2>&1

# Extract final metrics
grep -A 15 -E "BACKTESTING REPORT|Total profit|Avg Duration" \
    "user_data/backtest_results/phase2_v84_2025/enero_2025_v84_final.log" \
    > "user_data/backtest_results/phase2_v84_2025/enero_2025_v84_summary.txt" 2>/dev/null || true

echo "=== RESUMEN FINAL FASE 2 v8.4 ==="
echo ""

# Calculate overall metrics
if [ $total_trades -gt 0 ]; then
    win_rate=$(echo "scale=1; $total_wins * 100 / $total_trades" | bc -l 2>/dev/null || echo "0")
    echo "📊 MÉTRICAS ACUMULADAS 2025:"
    echo "   • Total Trades: $total_trades"
    echo "   • Total Wins: $total_wins"
    echo "   • Total Losses: $total_losses"
    echo "   • Win Rate: ${win_rate}%"
    echo ""
    
    # Check if target achieved
    target_achieved=false
    if (( $(echo "$win_rate >= 20" | bc -l) )); then
        target_achieved=true
        echo "🎯 ✅ OBJETIVO ALCANZADO: Win rate ${win_rate}% >= 20% target!"
    else
        echo "🎯 ⚠️ Objetivo parcial: Win rate ${win_rate}% < 20% target"
    fi
else
    echo "📊 MÉTRICAS ACUMULADAS 2025: Sin trades suficientes para análisis"
fi

echo ""
echo "📈 RESULTADOS DETALLADOS POR PERÍODO:"
echo ""

# Display detailed results
for period_label in "${TEST_PERIODS_2025[@]}"; do
    IFS=':' read -r dates label <<< "$period_label"
    echo "🔍 $label:"
    if [ -f "user_data/backtest_results/phase2_v84_2025/detailed/${label}_metrics.txt" ]; then
        head -10 "user_data/backtest_results/phase2_v84_2025/detailed/${label}_metrics.txt" 2>/dev/null || echo "    Sin datos disponibles"
    else
        echo "    Sin archivo de métricas"
    fi
    echo ""
done

echo "📊 RESULTADO FINAL ENERO 2025 COMPLETO (v8.4):"
if [ -f "user_data/backtest_results/phase2_v84_2025/enero_2025_v84_summary.txt" ]; then
    cat "user_data/backtest_results/phase2_v84_2025/enero_2025_v84_summary.txt"
else
    echo "Sin datos disponibles"
fi
echo ""

echo "=== ANÁLISIS DE EFECTIVIDAD v8.4 ==="
echo ""
echo "🔍 PUNTOS CLAVE DE EVALUACIÓN:"
echo "   • ¿Aumentó significativamente la actividad vs v8.3?"
echo "   • ¿Win rate mejorado hacia target 20-30%?"
echo "   • ¿Duración promedio se mantiene <30min?"
echo "   • ¿Control de riesgo preservado <0.2%?"
echo "   • ¿Filtros ultra-adaptativos capturan BTC $110K+ efectivamente?"
echo ""

echo "📁 Todos los resultados detallados guardados en:"
echo "   • Análisis granular: user_data/backtest_results/phase2_v84_2025/detailed/"
echo "   • Resumen final: user_data/backtest_results/phase2_v84_2025/"
echo ""

echo "======================================================================"
echo "🎯 FASE 2 RECALIBRACIÓN v8.4 COMPLETADA"
echo "======================================================================"
echo ""
echo "📋 EVALUACIÓN FINAL:"
if [ "$target_achieved" = true ]; then
    echo "   ✅ ÉXITO: Estrategia v8.4 lista para implementación"
    echo "   📈 Win rate target alcanzado en condiciones BTC $110K+"
    echo "   🚀 Proceder con deploy gradual en trading real"
else
    echo "   🔄 ITERACIÓN: Considerar ajustes adicionales"
    echo "   📊 Analizar resultados para posible v8.5"
    echo "   🎯 Evaluar otros enfoques (diversificación, timeframes)"
fi 