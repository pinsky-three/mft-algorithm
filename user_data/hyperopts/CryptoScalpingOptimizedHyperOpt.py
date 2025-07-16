# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401

"""
CryptoScalpingOptimized HyperOpt Class
=====================================

CONSERVATIVE OPTIMIZATION APPROACH - Avoid over-engineering
Based on memory: "Phase 3 Final with smart regime detection performed WORSE"

🎯 TARGET: Optimize existing successful strategy (+8.745 USDT) without breaking it
📊 CURRENT BASELINE: 254 trades, 1.457 USDT avg monthly profit

🔧 OPTIMIZATION PARAMETERS:
1. Market Health Thresholds (conservative ranges)
2. Entry Quality Filters (fine-tuning around current values)
3. ROI Ladder (risk/reward optimization)
4. Risk Management (stoploss, ATR ratios)

⚠️  RISK MITIGATION:
- Conservative parameter ranges (±20% from current values)
- Maintain market health architecture (proven successful)
- Focus on fine-tuning rather than radical changes
- Preserve pair-specific optimizations
"""

from freqtrade.optimize.hyperopt_interface import IHyperOpt
from skopt.space import Categorical, Dimension, Integer, Real


class CryptoScalpingOptimizedHyperOpt(IHyperOpt):
    """
    Conservative HyperOpt for CryptoScalpingOptimized
    Fine-tune around proven successful parameters
    """

    @staticmethod
    def roi_space() -> dict:
        """
        ROI optimization - Conservative adjustments to proven ladder
        Current: {"0": 0.025, "2": 0.020, "6": 0.015}
        """
        return {
            # Immediate ROI (current: 2.5%, range: 2.0%-3.5%)
            'roi_0': Real(0.020, 0.035, name='roi_0'),
            
            # 2-minute ROI (current: 2.0%, range: 1.5%-2.8%)  
            'roi_2': Real(0.015, 0.028, name='roi_2'),
            
            # 6-minute ROI (current: 1.5%, range: 1.0%-2.0%)
            'roi_6': Real(0.010, 0.020, name='roi_6'),
        }

    @staticmethod
    def stoploss_space() -> dict:
        """
        Stoploss optimization - Conservative range around current -2.5%
        Range: -3.5% to -2.0% (avoid too tight or too loose)
        """
        return {
            'stoploss': Real(-0.035, -0.020, name='stoploss'),
        }

    @staticmethod
    def buy_space() -> dict:
        """
        Define the hyperparameter search space with conservative ranges
        All ranges centered around current successful values
        """
        return {
            # === MARKET HEALTH THRESHOLDS (Core Strategy) ===
            'min_market_health': Real(0.4, 0.6, name='min_market_health'),        # Current: 0.5
            'min_trend_quality': Real(0.15, 0.25, name='min_trend_quality'),       # Current: 0.2
            'max_choppiness': Real(0.6, 0.8, name='max_choppiness'),               # Current: 0.7
            
            # === ENTRY QUALITY FILTERS ===
            'min_volume_ratio': Real(1.7, 2.1, name='min_volume_ratio'),           # Current: 1.9
            'rsi_threshold': Integer(52, 62, name='rsi_threshold'),                 # Current: 57
            'entry_rsi_threshold': Integer(55, 65, name='entry_rsi_threshold'),     # Current: 58
            'momentum_strength': Real(0.70, 0.85, name='momentum_strength'),       # Current: 0.78
            'min_atr_ratio': Real(0.0020, 0.0025, name='min_atr_ratio'),          # Current: 0.0022
            
            # === PRECISION TUNING ===
            'level_proximity': Real(0.003, 0.007, name='level_proximity'),         # Current: 0.005
            
            # === ADAPTIVE FILTERING (New Optimization) ===
            'adaptive_health_threshold': Real(0.55, 0.65, name='adaptive_health_threshold'),    # When to apply adaptive filtering
            'adaptive_penalty_multiplier': Real(1.1, 1.3, name='adaptive_penalty_multiplier'), # How much to penalize in poor conditions
            
            # === SESSION OPTIMIZATION (Enable/Disable Features) ===
            'enable_eth_enhancement': Categorical([True, False], name='enable_eth_enhancement'),     # ETH-specific optimizations
            'enable_sol_tightening': Categorical([True, False], name='enable_sol_tightening'),       # SOL-specific restrictions
            'enable_session_filter': Categorical([True, False], name='enable_session_filter'),       # London/NY session filtering
        }

# === HYPEROPT USAGE INSTRUCTIONS ===
"""
🚀 USAGE COMMANDS:

1. HYPEROPT OPTIMIZATION:
   docker compose run --rm freqtrade hyperopt \\
     --strategy CryptoScalpingOptimizedHyperopt \\
     --hyperopt CryptoScalpingOptimizedHyperOpt \\
     --hyperopt-loss SharpeHyperOptLoss \\
     --epochs 100 \\
     --timerange 20250101-20250601 \\
     --spaces buy roi stoploss

2. SPECIFIC SPACE OPTIMIZATION:
   # Market Health Only
   --spaces buy
   
   # ROI Ladder Only  
   --spaces roi
   
   # Risk Management Only
   --spaces stoploss
   
   # Indicators Only
   --spaces indicator

3. CONSERVATIVE APPROACH:
   Start with --epochs 50 to avoid overfitting
   Use SharpeHyperOptLoss for risk-adjusted returns
   Test on 5-month period (Jan-May 2025)
   Validate on June 2025

4. VALIDATION:
   After optimization, test optimized parameters on June 2025
   Ensure monthly profit remains positive
   Verify trade count doesn't drop below 150 (current: 254)

📊 EXPECTED IMPROVEMENTS:
- 10-20% profit increase (target: 10+ USDT vs current 8.745 USDT)
- Maintain or improve win rate
- Preserve monthly consistency
- Avoid negative months (like March: -4.668 USDT)

⚠️  AVOID OVER-OPTIMIZATION:
- Don't optimize on full 6-month period (use 5 months max)
- Keep 1 month for out-of-sample validation
- If optimized strategy performs worse than baseline, reject it
- Remember: "smart regime detection performed WORSE"
""" 