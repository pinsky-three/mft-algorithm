# Phase 3 Balanced - Calibrated thresholds for optimal consistency/profitability balance
# Copy from CryptoScalpingPhase3.py and adjust key parameters

# This is Phase 3 with balanced thresholds:
# - Market Health: 0.65 (vs 0.7 in strict version)  
# - Volume Quality: 0.75 (vs 0.85 in strict version)
# - Entry Selectivity: 0.75 (vs 0.85 in strict version)
# - Smart Money Threshold: 0.65 (vs 0.75 in strict version)
# - Performance Lookback: 20 (vs 25 in strict version)
# - Market Regime Strictness: 0.7 (vs 0.8 in strict version)

# Import all the same code from Phase 3 but with adjusted constants
exec(open('user_data/strategies/CryptoScalpingPhase3.py').read())

# Override the strict constants with balanced values
class CryptoScalpingPhase3Balanced(CryptoScalpingPhase3):
    """
    PHASE 3 BALANCED - Calibrated thresholds for consistency + profitability
    """
    
    # === BALANCED PARAMETERS (vs strict Phase 3) ===
    MIN_SMART_MONEY_FLOW = 0.65      # 0.75 → 0.65 (relaxed)
    MIN_VOLUME_QUALITY = 0.75        # 0.8 → 0.75 (relaxed)  
    MIN_MARKET_HEALTH = 0.65         # 0.7 → 0.65 (relaxed)
    MIN_PERFORMANCE_SCORE = 0.65     # 0.7 → 0.65 (relaxed)
    MAX_MONTHLY_TRADES = 80          # Keep same (prevent overtrading)
    
    # === HYPEROPT PARAMETERS (Balanced defaults) ===
    smart_money_threshold = DecimalParameter(0.5, 0.8, default=0.65, space="buy")      # 0.75 → 0.65
    volume_quality_min = DecimalParameter(0.7, 0.9, default=0.75, space="buy")        # 0.85 → 0.75
    performance_lookback = IntParameter(15, 30, default=20, space="buy")              # 25 → 20
    win_rate_threshold = DecimalParameter(0.65, 0.8, default=0.7, space="buy")        # 0.75 → 0.7
    market_regime_strictness = DecimalParameter(0.6, 0.8, default=0.7, space="buy")   # 0.8 → 0.7
    entry_selectivity = DecimalParameter(0.7, 0.9, default=0.75, space="buy")         # 0.85 → 0.75 