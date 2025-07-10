#!/bin/bash

# Test Realista 2025 - MultiHorizonMomentum Strategy v8.2 SCALPER
# Validación con datos actuales de 2025 para comprobar robustez en mercado real

echo "=================================================================="
echo "🚀 TEST REALISTA 2025 - MultiHorizonMomentum v8.2 SCALPER"
echo "=================================================================="
echo ""
echo "🎯 OBJETIVOS DE LA PRUEBA 2025:"
echo "   • Validar robustez con datos más recientes (Enero 2025)"
echo "   • Confirmar efectividad en condiciones de mercado actuales" 
echo "   • Probar scalping con BTC a $113K+ (niveles históricos)"
echo "   • Verificar que los filtros funcionan en alta volatilidad"
echo ""

# Test parameters
STRATEGY="MultiHorizonMomentum"
PAIRS="BTC/USDT"
TIMEFRAME="1m"
FEE="0.0002"  # 0.02% realistic fees (Binance maker)

echo "📊 CONFIGURACIÓN DE PRUEBA:"
echo "   Strategy: $STRATEGY v8.2 SCALPER"
echo "   Pairs: $PAIRS"
echo "   Timeframe: $TIMEFRAME" 
echo "   Fees: $(echo "scale=3; $FEE*100" | bc)% (Binance maker realistic)"
echo ""

# Test periods for 2025
declare -a PERIODS_2025=(
    "20250101-20250107:Semana-1-2025"
    "20250108-20250113:Semana-2-2025"
    "20250101-20250113:Enero-2025-Complete"
)

echo "🗓️ PERÍODOS DE PRUEBA 2025:"
for period in "${PERIODS_2025[@]}"; do
    range=$(echo $period | cut -d: -f1)
    label=$(echo $period | cut -d: -f2)
    echo "   • $label: $range"
done
echo ""

# Create results directory
RESULTS_DIR="user_data/backtest_results/test_2025_realista"
mkdir -p "$RESULTS_DIR"

echo "=== INICIANDO BACKTESTS 2025 ==="
echo ""

for period in "${PERIODS_2025[@]}"; do
    range=$(echo $period | cut -d: -f1)
    label=$(echo $period | cut -d: -f2)
    
    echo ">>> Testeando período: $label ($range)"
    
    # Run backtest with fees
    echo "    Ejecutando con fees realistas..."
    docker compose run --rm freqtrade backtesting \
        --strategy $STRATEGY \
        --pairs $PAIRS \
        --timeframe $TIMEFRAME \
        --fee $FEE \
        --timerange $range \
        --cache=none \
        --export trades \
        --export-filename "${RESULTS_DIR}/${label}_with_fees" \
        > "${RESULTS_DIR}/${label}_with_fees.log" 2>&1
    
    if [ $? -eq 0 ]; then
        echo "    ✅ Backtest completado: ${RESULTS_DIR}/${label}_with_fees.log"
        
        # Extract key metrics
        echo "    📈 Extrayendo métricas..."
        grep -A 10 -E "Total profit|Win.*Draw.*Loss|Avg Duration" "${RESULTS_DIR}/${label}_with_fees.log" | head -15 > "${RESULTS_DIR}/${label}_metrics.txt"
        
    else
        echo "    ❌ Error en backtest para $label"
    fi
    echo ""
done

echo "=== RESUMEN DE RESULTADOS 2025 ==="
echo ""

for period in "${PERIODS_2025[@]}"; do
    label=$(echo $period | cut -d: -f2)
    range=$(echo $period | cut -d: -f1)
    
    echo "📊 $label ($range):"
    
    if [ -f "${RESULTS_DIR}/${label}_metrics.txt" ]; then
        cat "${RESULTS_DIR}/${label}_metrics.txt" | grep -E "Total profit|Win.*Draw.*Loss|Avg Duration" | while read line; do
            echo "    $line"
        done
    else
        echo "    ❌ No hay resultados disponibles"
    fi
    echo ""
done

echo "=== ANÁLISIS COMPARATIVO ==="
echo ""
echo "🔍 PUNTOS CLAVE A ANALIZAR:"
echo "   • ¿Mantiene el comportamiento consistente de 2024?"
echo "   • ¿Los filtros TEMA+ADX+CMO siguen siendo efectivos?"
echo "   • ¿El scalping funciona con BTC a $113K+?"
echo "   • ¿Win rate se mantiene en rango 15-50%?"
echo "   • ¿Duración promedio <30min para scalping?"
echo ""

echo "📁 Todos los resultados guardados en: $RESULTS_DIR/"
echo ""
echo "=================================================================="
echo "🎯 TEST 2025 COMPLETADO - Revisa los resultados para validación"
echo "==================================================================" 