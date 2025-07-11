#!/usr/bin/env python3
"""
BTC Volatility Analysis 2025 vs 2024 - Phase 3 Advanced Optimization
==================================================================

Analysis for MultiHorizonMomentum v8.5 optimization:
- Compare volatility patterns 2024 vs 2025
- Identify optimal ATR targets for BTC $110K+ conditions
- Recommend timeframe adjustments for high liquidity environment
- Provide data-driven optimization recommendations

Target: Make strategy profitable in 2025 conditions
"""

import json
import math
from datetime import datetime, timedelta
from pathlib import Path

class BTCVolatilityAnalyzer:
    """Analyze BTC volatility patterns for strategy optimization."""
    
    def __init__(self):
        self.data_path = Path("user_data/data/binance")
        self.results = {}
        
    def load_data(self, timeframe="1d"):
        """Load BTC/USDT data from JSON files."""
        file_path = self.data_path / f"BTC_USDT-{timeframe}.json"
        
        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")
            
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        # Convert data to proper format
        processed_data = []
        for row in data:
            processed_data.append({
                'timestamp': datetime.fromtimestamp(row[0] / 1000),
                'open': float(row[1]),
                'high': float(row[2]),
                'low': float(row[3]),
                'close': float(row[4]),
                'volume': float(row[5])
            })
            
        return processed_data
    
    def calculate_volatility_metrics(self, data):
        """Calculate comprehensive volatility metrics."""
        for i, row in enumerate(data):
            if i == 0:
                row['true_range'] = row['high'] - row['low']
                row['returns'] = 0
            else:
                prev_close = data[i-1]['close']
                high_low = row['high'] - row['low']
                high_close = abs(row['high'] - prev_close)
                low_close = abs(row['low'] - prev_close)
                row['true_range'] = max(high_low, high_close, low_close)
                row['returns'] = (row['close'] - prev_close) / prev_close
                
            # Intraday range
            row['intraday_range'] = (row['high'] - row['low']) / row['close']
            
            # ATR calculation (simple moving average)
            if i >= 14:
                atr_14_sum = sum(data[j]['true_range'] for j in range(i-13, i+1))
                row['atr_14'] = atr_14_sum / 14
            else:
                row['atr_14'] = None
                
            if i >= 100:
                atr_100_sum = sum(data[j]['true_range'] for j in range(i-99, i+1))
                row['atr_100'] = atr_100_sum / 100
            else:
                row['atr_100'] = None
                
            # Volatility calculation
            if i >= 14:
                returns_14 = [data[j]['returns'] for j in range(i-13, i+1)]
                mean_ret = sum(returns_14) / 14
                variance = sum((r - mean_ret) ** 2 for r in returns_14) / 14
                row['volatility_14'] = math.sqrt(variance) * math.sqrt(24*60)  # Annualized
            else:
                row['volatility_14'] = None
                
        return data
    
    def analyze_by_periods(self, data):
        """Analyze volatility by different time periods."""
        periods = {
            '2024_all': [row for row in data if row['timestamp'].year == 2024],
            '2025_all': [row for row in data if row['timestamp'].year == 2025],
            'btc_110k_plus': [row for row in data if row['close'] > 110000]
        }
        
        analysis = {}
        for period_name, period_data in periods.items():
            if len(period_data) == 0:
                continue
                
            # Filter out None values for calculations
            valid_atr_14 = [row['atr_14'] for row in period_data if row['atr_14'] is not None]
            valid_atr_100 = [row['atr_100'] for row in period_data if row['atr_100'] is not None]
            valid_vol = [row['volatility_14'] for row in period_data if row['volatility_14'] is not None]
            valid_intraday = [row['intraday_range'] for row in period_data]
            
            prices = [row['close'] for row in period_data]
            
            analysis[period_name] = {
                'count': len(period_data),
                'avg_price': sum(prices) / len(prices) if prices else 0,
                'min_price': min(prices) if prices else 0,
                'max_price': max(prices) if prices else 0,
                'avg_atr_14': sum(valid_atr_14) / len(valid_atr_14) if valid_atr_14 else 0,
                'avg_atr_100': sum(valid_atr_100) / len(valid_atr_100) if valid_atr_100 else 0,
                'atr_price_ratio': (sum(valid_atr_14) / len(valid_atr_14)) / (sum(prices) / len(prices)) if valid_atr_14 and prices else 0,
                'avg_volatility': sum(valid_vol) / len(valid_vol) if valid_vol else 0,
                'avg_intraday_vol': sum(valid_intraday) / len(valid_intraday) if valid_intraday else 0,
            }
            
        return analysis
    
    def recommend_atr_targets(self, analysis):
        """Recommend ATR targets based on volatility analysis."""
        recommendations = {}
        
        # Get high price period metrics
        if 'btc_110k_plus' in analysis and analysis['btc_110k_plus']['count'] > 0:
            high_price = analysis['btc_110k_plus']
            volatility_factor = high_price['avg_volatility']
            
            # Current targets: TP=2.5x, SL=1.5x, Trail=1.2x
            # Adjust based on volatility
            base_volatility = 0.05  # 5% baseline
            
            if volatility_factor > base_volatility * 1.5:  # High vol
                tp_multiplier = 3.5   # Increase TP for volatile conditions
                sl_multiplier = 2.2   # Increase SL for whipsaws
                trail_multiplier = 1.8
                vol_regime = 'high'
            elif volatility_factor < base_volatility * 0.7:  # Low vol
                tp_multiplier = 1.8   # Decrease TP for tight markets
                sl_multiplier = 1.0   # Decrease SL for precision
                trail_multiplier = 0.8
                vol_regime = 'low'
            else:  # Normal vol
                tp_multiplier = 2.5
                sl_multiplier = 1.5
                trail_multiplier = 1.2
                vol_regime = 'normal'
                
            recommendations['atr_targets'] = {
                'take_profit': tp_multiplier,
                'stop_loss': sl_multiplier,
                'trailing_stop': trail_multiplier,
                'volatility_analysis': {
                    'current_vol': volatility_factor,
                    'base_vol': base_volatility,
                    'vol_regime': vol_regime
                }
            }
        
        return recommendations
    
    def analyze_optimal_timeframes(self, analysis):
        """Analyze optimal timeframes for different market conditions."""
        recommendations = {}
        
        if 'btc_110k_plus' in analysis and analysis['btc_110k_plus']['count'] > 0:
            high_price = analysis['btc_110k_plus']
            avg_vol = high_price['avg_volatility']
            
            if avg_vol > 0.08:  # Very high volatility
                recommendations['timeframes'] = {
                    'primary': '1m',
                    'secondary': '5m',
                    'trend_filter': '15m',
                    'reason': 'High volatility requires faster reaction times'
                }
            elif avg_vol < 0.03:  # Low volatility
                recommendations['timeframes'] = {
                    'primary': '5m',
                    'secondary': '15m', 
                    'trend_filter': '1h',
                    'reason': 'Low volatility allows longer timeframes for better signals'
                }
            else:  # Normal volatility
                recommendations['timeframes'] = {
                    'primary': '1m',
                    'secondary': '15m',
                    'trend_filter': '1h',
                    'reason': 'Balanced approach for normal volatility'
                }
                
        return recommendations
    
    def generate_report(self):
        """Generate comprehensive volatility analysis report."""
        print("🔍 BTC VOLATILITY ANALYSIS - PHASE 3 OPTIMIZATION")
        print("=" * 60)
        
        # Load and analyze data
        print("📊 Loading BTC data...")
        try:
            data_daily = self.load_data("1d")
            data_4h = self.load_data("4h")
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return None
        
        print("📈 Calculating volatility metrics...")
        data_daily = self.calculate_volatility_metrics(data_daily)
        data_4h = self.calculate_volatility_metrics(data_4h)
        
        print("📋 Analyzing by periods...")
        analysis_daily = self.analyze_by_periods(data_daily)
        analysis_4h = self.analyze_by_periods(data_4h)
        
        # Print results
        self.print_analysis_results(analysis_daily, "DAILY")
        self.print_analysis_results(analysis_4h, "4H")
        
        # Generate recommendations
        print("\n🎯 OPTIMIZATION RECOMMENDATIONS")
        print("=" * 40)
        
        atr_recs = self.recommend_atr_targets(analysis_daily)
        timeframe_recs = self.analyze_optimal_timeframes(analysis_daily)
        
        if 'atr_targets' in atr_recs:
            targets = atr_recs['atr_targets']
            print(f"📌 ATR TARGETS for BTC >$110K:")
            print(f"   Take Profit: {targets['take_profit']:.1f}x ATR")
            print(f"   Stop Loss: {targets['stop_loss']:.1f}x ATR") 
            print(f"   Trailing: {targets['trailing_stop']:.1f}x ATR")
            print(f"   Volatility Regime: {targets['volatility_analysis']['vol_regime'].upper()}")
            
        if 'timeframes' in timeframe_recs:
            tf = timeframe_recs['timeframes']
            print(f"\n⏱️ OPTIMAL TIMEFRAMES:")
            print(f"   Primary: {tf['primary']}")
            print(f"   Secondary: {tf['secondary']}")
            print(f"   Trend Filter: {tf['trend_filter']}")
            print(f"   Reason: {tf['reason']}")
            
        # Store results for strategy implementation
        self.results = {
            'analysis_daily': analysis_daily,
            'analysis_4h': analysis_4h,
            'atr_recommendations': atr_recs,
            'timeframe_recommendations': timeframe_recs
        }
        
        return self.results
    
    def print_analysis_results(self, analysis, timeframe_name):
        """Print formatted analysis results."""
        print(f"\n📊 {timeframe_name} ANALYSIS RESULTS")
        print("-" * 30)
        
        for period, data in analysis.items():
            if data['count'] == 0:
                continue
                
            print(f"\n🗓️ {period.upper()}:")
            print(f"   Samples: {data['count']}")
            print(f"   Avg Price: ${data['avg_price']:,.0f}")
            print(f"   Price Range: ${data['min_price']:,.0f} - ${data['max_price']:,.0f}")
            print(f"   ATR(14): ${data['avg_atr_14']:,.0f}")
            print(f"   ATR/Price: {data['atr_price_ratio']:.4f}")
            print(f"   Volatility: {data['avg_volatility']:.4f}")
            print(f"   Intraday Vol: {data['avg_intraday_vol']:.4f}")

def main():
    """Run the complete volatility analysis."""
    analyzer = BTCVolatilityAnalyzer()
    results = analyzer.generate_report()
    
    if results:
        print("\n✅ Analysis complete! Results stored for strategy optimization.")
        print("🚀 Ready to implement v8.5 with optimized parameters.")
    else:
        print("\n❌ Analysis failed. Check data files.")
    
    return results

if __name__ == "__main__":
    main() 