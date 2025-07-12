# FreqTrade Backtest Analyzer Dashboard

A comprehensive Streamlit-based technical analysis dashboard for analyzing your Multi-Horizon Momentum Strategy backtest results.

## 🚀 Features

### 📊 Performance Overview
- **Key Metrics**: Total trades, win rate, total return, Sharpe ratio
- **Risk Metrics**: Maximum drawdown, CAGR, expectancy, profit factor
- **Trade Distribution**: Visual breakdown of wins, losses, and draws
- **Pair Performance**: Individual performance analysis per trading pair

### 📈 Trade Analysis
- **Exit Reason Analysis**: Understand why trades are closed
- **Holding Time Analysis**: Average holding periods for winners vs losers
- **Consecutive Performance**: Max consecutive wins/losses tracking
- **Market Comparison**: Strategy performance vs market movement

### ⚠️ Risk Management
- **Drawdown Analysis**: Detailed drawdown metrics and timing
- **Performance Ratios**: Sharpe, Sortino, Calmar, and SQN ratios
- **Risk-Adjusted Returns**: Comprehensive risk assessment

### 🔍 Algorithm Insights
- **Automated Analysis**: AI-powered insights and recommendations
- **Strategy-Specific Tips**: Tailored advice for Multi-Horizon Momentum
- **Optimization Suggestions**: Data-driven parameter tuning recommendations
- **Performance Alerts**: Critical issues and success indicators

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- FreqTrade backtest results in `user_data/backtest_results/`

### Install Dependencies
```bash
# Using uv (recommended)
uv add streamlit plotly pandas numpy

# Or using pip
pip install streamlit plotly pandas numpy
```

## 🎯 Usage

### Quick Start
```bash
# Run the dashboard
python run_analyzer.py

# Or directly with streamlit
streamlit run backtest_analyzer.py
```

The dashboard will open in your browser at `http://localhost:8501`

### Dashboard Navigation
1. **File Selection**: Choose backtest results from the sidebar
2. **Overview Tab**: High-level performance metrics and charts
3. **Trade Analysis Tab**: Detailed trade breakdown and exit reasons
4. **Risk Metrics Tab**: Comprehensive risk assessment
5. **Insights Tab**: AI-powered analysis and recommendations

## 📁 Data Requirements

The analyzer expects FreqTrade backtest results in this structure:
```
user_data/backtest_results/
├── backtest-result-2025-07-10_17-26-08.zip
├── backtest-result-2025-07-10_17-26-08.meta.json
└── ... (more backtest files)
```

Each zip file should contain:
- `backtest-result-*.json` (main results)
- `backtest-result-*_config.json` (configuration)
- Strategy Python file
- Market change data

## 🎛️ Key Metrics Explained

### Performance Metrics
- **Win Rate**: Percentage of profitable trades
- **Total Return**: Overall strategy performance
- **Sharpe Ratio**: Risk-adjusted returns (>1.5 excellent, <0.5 poor)
- **CAGR**: Compound Annual Growth Rate
- **Expectancy**: Average profit/loss per trade
- **Profit Factor**: Ratio of gross profit to gross loss

### Risk Metrics
- **Max Drawdown**: Largest peak-to-trough decline
- **Sortino Ratio**: Downside deviation adjusted returns
- **Calmar Ratio**: Annual return vs max drawdown
- **SQN**: System Quality Number (trading system robustness)

## 🔧 Troubleshooting

### No Backtest Files Found
```
❌ No backtest result files found in user_data/backtest_results/
```
**Solution**: Run backtests first using your test scripts:
```bash
./test_BREAKEVEN_v7.sh
./test_ULTIMATE_v6.sh
```

### No Trades Executed
If you see "No trades executed in this backtest":
- Strategy filters may be too restrictive
- Consider adjusting RSI threshold (currently 60)
- Reduce volume multiplier (currently 2.0x)
- Check 15m directional filter alignment

### Performance Issues
- The dashboard loads the last 20 backtest files for performance
- Large backtest files may take longer to load
- Use the file selection dropdown to choose specific results

## 🎨 Customization

### Adding New Metrics
Extend the `create_performance_metrics_card()` function to add custom metrics:

```python
def create_custom_metric(stats: StrategyStats) -> None:
    custom_value = calculate_custom_metric(stats)
    st.metric("Custom Metric", format_number(custom_value))
```

### Custom Insights
Add strategy-specific insights in `create_algorithm_insights()`:

```python
# Custom insight example
if custom_condition:
    insights.append("🟢 **Custom Insight**: Your analysis here")
```

## 📊 Multi-Horizon Momentum Specific Insights

The analyzer provides specialized insights for your strategy:

### Entry Conditions Analysis
- **RSI Filter**: Monitors RSI > 60 effectiveness
- **Volume Filter**: Analyzes 2.0x volume multiplier impact
- **EMA Alignment**: Triple EMA (30/120/360) trend confirmation
- **15m Directional Filter**: Micro-trend alignment effectiveness

### Exit Strategy Analysis
- **ATR Take-Profit**: 3.5x ATR target analysis
- **ATR Stop-Loss**: 2x ATR risk management
- **Trailing Stop**: 1.5x ATR trailing effectiveness
- **Exit Signal Elimination**: Confirms pure ATR exit approach

### Optimization Recommendations
- **Entry Relaxation**: Suggests RSI/volume adjustments for low trade frequency
- **Exit Optimization**: Recommends TP/SL ratio improvements
- **Risk Management**: Position sizing and stop-loss positioning advice

## 🤝 Contributing

To extend the analyzer:
1. Add new visualization functions
2. Implement additional metrics calculations
3. Enhance the insights engine
4. Add export functionality for reports

## 📝 License

This analyzer is designed specifically for the Multi-Horizon Momentum Strategy project and FreqTrade integration.

---

**Happy Trading! 📈**

For questions or issues, check the debug tab in the dashboard for raw data inspection. 