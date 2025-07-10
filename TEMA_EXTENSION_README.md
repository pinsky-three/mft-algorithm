# MultiHorizonMomentum Strategy v8 - TEMA Extended

## Resumen de Cambios

Tu estrategia original ha sido exitosamente extendida con los elementos de la estrategia TEMA de Jesse. La nueva versión v8 combina lo mejor de ambos enfoques para maximizar la precisión de las entradas y mejorar la gestión de riesgo.

## 🚀 Nuevas Características

### 1. **Indicadores TEMA Añadidos**
- **TEMA 10/80** (1m): Crossover de corto plazo para señales de entrada
- **TEMA 20/70** (4h): Filtro de tendencia de largo plazo 

### 2. **Filtros de Momentum Mejorados**
- **ADX > 40**: Confirma fuerza de tendencia antes de entrar
- **CMO > 40** (long) / **CMO < -40** (short): Direccionalidad del momentum

### 3. **Soporte para Trading en Corto**
- Lógica completa para posiciones SHORT (opcional)
- Gestión de riesgo ATR adaptada para ambas direcciones
- Control via flag `can_short = True/False`

### 4. **Gestión de Riesgo Mejorada**
- Stop Loss: 2.0 ATR desde entrada (ambas direcciones)
- Take Profit: 3.5 ATR desde entrada (conservador y alcanzable)
- Trailing Stop: 1.5 ATR una vez en beneficio
- Soporte completo para long y short

## 📊 Condiciones de Entrada

### Posiciones LONG (Compra)
Todas las condiciones deben cumplirse:
- ✅ Triple EMA alignment: `EMA30 > EMA120 > EMA360`
- ✅ TEMA short-term uptrend: `TEMA10 > TEMA80`
- ✅ TEMA long-term uptrend: `TEMA20_4h > TEMA70_4h`
- ✅ Strong momentum: `ADX > 40` AND `CMO > 40`
- ✅ RSI momentum: `RSI > 60`
- ✅ MACD bullish: `MACD > Signal`
- ✅ Volume surge: `Volume > 2x average`
- ✅ 15m alignment: `EMA30_15m > EMA120_15m`

### Posiciones SHORT (Venta) - Opcional
Todas las condiciones deben cumplirse:
- ✅ Triple EMA downtrend: `EMA30 < EMA120 < EMA360`
- ✅ TEMA short-term downtrend: `TEMA10 < TEMA80`
- ✅ TEMA long-term downtrend: `TEMA20_4h < TEMA70_4h`
- ✅ Strong momentum: `ADX > 40` AND `CMO < -40`
- ✅ RSI bearish: `RSI < 40`
- ✅ MACD bearish: `MACD < Signal`
- ✅ Volume surge: `Volume > 2x average`
- ✅ 15m alignment: `EMA30_15m < EMA120_15m`

## ⚙️ Configuración

### Flags de Control
```python
USE_TEMA_FILTER: bool = True      # Habilitar filtros TEMA
USE_ADX_CMO_FILTER: bool = True   # Habilitar filtros ADX/CMO
can_short: bool = False           # Habilitar trading en corto
```

### Timeframes Utilizados
- **Principal**: 1m (entradas y indicadores principales)
- **Filtro direccional**: 15m (EMAs de confirmación)
- **Tendencia largo plazo**: 4h (TEMA crossover)

## 🧪 Testing

### Script de Prueba
```bash
# Ejecutar backtest completo
./test_tema_extended_v8.sh
```

### Comandos Manuales
```bash
# Con fees realistas
freqtrade backtesting -s MultiHorizonMomentum -p BTC/USDT,ETH/USDT --fee 0.1 --timeframe 1m

# Sin fees (validación de edge)
freqtrade backtesting -s MultiHorizonMomentum -p BTC/USDT,ETH/USDT --fee 0 --timeframe 1m
```

## 📈 Expectativas de Rendimiento

### Mejoras Esperadas
- **Mayor Precisión**: Combinación de EMA + TEMA reduce señales falsas
- **Mejor Win Rate**: Filtros ADX/CMO eliminan trades en mercados laterales  
- **Gestión de Riesgo Superior**: ATR dinámico optimizado para ambas direcciones
- **Flexibilidad**: Capacidad de operar tanto long como short

### Características Conservadas
- **ATR-based exits**: Sistema probado con 47.2% win rate
- **Volume filtering**: Solo trades en liquidez premium
- **Multi-timeframe**: Confirmación en 1m, 15m, y 4h
- **Conservative TP/SL**: Risk/Reward 1:1.75 optimizado

## 🔧 Personalización

### Para Habilitar Trading en Corto
```python
can_short: bool = True  # Cambiar a True en la clase
```

### Para Ajustar Agresividad  
```python
# Más agresivo (más trades)
cond_adx = dataframe["adx"] > 30  # Reducir de 40 a 30
cond_rsi_long = dataframe["rsi"] > 55  # Reducir de 60 a 55

# Más conservador (menos trades)
cond_adx = dataframe["adx"] > 50  # Aumentar de 40 a 50
cond_rsi_long = dataframe["rsi"] > 65  # Aumentar de 60 a 65
```

### Para Ajustar Risk/Reward
```python
# En custom_exit()
tp_price = entry + 4.0 * atr  # Más conservador (de 3.5 a 4.0)
sl_trail = entry + 2.0 * atr  # Trailing más amplio (de 1.5 a 2.0)
```

## 📝 Próximos Pasos

1. **Ejecutar backtest**: `./test_tema_extended_v8.sh`
2. **Analizar resultados**: Comparar con versión v7 original
3. **Ajustar parámetros**: Según performance observada
4. **Testing en paper trading**: Antes de live trading
5. **Considerar habilitar shorts**: Si el mercado lo permite

La estrategia ahora combina lo mejor de ambos mundos: la robustez probada de tu sistema original con la precisión de los filtros TEMA y momentum. ¡Está lista para testing! 🚀 