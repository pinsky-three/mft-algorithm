#!/usr/bin/env python3
"""
FreqTrade Backtest Results Analyzer
===================================

Technical analysis dashboard for Multi-Horizon Momentum Strategy results.
Provides comprehensive insights into algorithm performance, trade analysis,
and optimization opportunities.
"""

import json
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


# Type definitions
BacktestData = Dict[str, Any]
TradeData = Dict[str, Any]
StrategyStats = Dict[str, Union[str, int, float]]


class BacktestAnalyzer:
    """Main analyzer class for FreqTrade backtest results."""
    
    def __init__(self):
        self.backtest_data: Optional[BacktestData] = None
        self.trades_df: Optional[pd.DataFrame] = None
        self.market_data: Optional[pd.DataFrame] = None
        
    def load_backtest_file(self, file_path: str) -> bool:
        """Load backtest results from file."""
        try:
            file_path = Path(file_path)
            
            if file_path.suffix == '.zip':
                # Extract JSON from zip file
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    # Find the main backtest results file (not config or other files)
                    json_files = [f for f in zip_ref.namelist() 
                                 if f.endswith('.json') 
                                 and not f.endswith('_config.json')
                                 and not f.endswith('.meta.json')]
                    
                    if not json_files:
                        st.error("No main backtest results file found in ZIP archive")
                        return False
                    
                    # Prefer the file that matches the zip name pattern
                    main_file = None
                    zip_basename = file_path.stem  # e.g., "backtest-result-2025-07-11_03-20-25"
                    
                    for json_file in json_files:
                        if json_file.startswith(zip_basename) and json_file.endswith('.json'):
                            main_file = json_file
                            break
                    
                    # Fallback to first JSON file if no matching pattern
                    if not main_file:
                        main_file = json_files[0]
                    
                    print(f"Loading main backtest file: {main_file}")
                    
                    with zip_ref.open(main_file) as json_file:
                        self.backtest_data = json.loads(json_file.read().decode('utf-8'))
            else:
                # Load JSON file directly
                with open(file_path, 'r') as f:
                    self.backtest_data = json.load(f)
            
            # Validate loaded data
            if not isinstance(self.backtest_data, dict):
                st.error("Invalid backtest data format - not a dictionary")
                return False
                
            # Check for required keys
            if 'strategy' not in self.backtest_data:
                st.error("No strategy data found in backtest file")
                return False
                
            # Verify strategy data is a dictionary
            if not isinstance(self.backtest_data['strategy'], dict):
                st.error(f"Strategy data is not a dictionary: {type(self.backtest_data['strategy'])}")
                return False
                
            # Process trades if available
            self._process_trades()
            
            # Debug info
            print(f"Loaded backtest data with keys: {list(self.backtest_data.keys())}")
            if 'strategy' in self.backtest_data:
                print(f"Strategy keys: {list(self.backtest_data['strategy'].keys())}")
            
            return True
            
        except Exception as e:
            st.error(f"Error loading backtest file: {str(e)}")
            print(f"Detailed error: {e}")
            return False
    
    def load_market_data(self, pair: str, timeframe: str = "1m") -> bool:
        """Load market data for the given pair and timeframe."""
        try:
            data_path = Path(f"user_data/data/binance/{pair.replace('/', '_')}-{timeframe}.json")
            
            if data_path.exists():
                with open(data_path, 'r') as f:
                    raw_data = json.load(f)
                
                # Convert to DataFrame with proper column names
                if isinstance(raw_data, list) and len(raw_data) > 0:
                    columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    self.market_data = pd.DataFrame(raw_data, columns=columns)
                    
                    # Convert timestamp to datetime
                    self.market_data['datetime'] = pd.to_datetime(self.market_data['timestamp'], unit='ms')
                    self.market_data.set_index('datetime', inplace=True)
                    
                    # Ensure numeric columns
                    for col in ['open', 'high', 'low', 'close', 'volume']:
                        self.market_data[col] = pd.to_numeric(self.market_data[col])
                        
                    return True
                    
        except Exception as e:
            st.error(f"Error loading market data: {e}")
            
        return False
        
    def _process_trades(self):
        """Process trades from backtest data into DataFrame."""
        try:
            if not self.backtest_data or 'strategy' not in self.backtest_data:
                print("No backtest data or strategy section found")
                return
                
            strategy_section = self.backtest_data['strategy']
            if not isinstance(strategy_section, dict):
                print(f"Strategy section is not a dict: {type(strategy_section)}")
                return
                
            all_trades = []
            for strategy_name, strategy_data in strategy_section.items():
                if not isinstance(strategy_data, dict):
                    print(f"Strategy data for {strategy_name} is not a dict: {type(strategy_data)}")
                    continue
                    
                # Get trades from strategy data
                if 'trades' in strategy_data and isinstance(strategy_data['trades'], list):
                    trades = strategy_data['trades']
                    print(f"Found {len(trades)} trades in {strategy_name}")
                    
                    for trade in trades:
                        # Add strategy name to each trade
                        trade_with_strategy = trade.copy()
                        trade_with_strategy['strategy'] = strategy_name
                        all_trades.append(trade_with_strategy)
                else:
                    print(f"No trades found in {strategy_name}")
            
            if all_trades:
                # Convert to DataFrame
                self.trades_df = pd.DataFrame(all_trades)
                
                # Convert timestamps to datetime
                if 'open_timestamp' in self.trades_df.columns:
                    self.trades_df['open_datetime'] = pd.to_datetime(
                        self.trades_df['open_timestamp'], unit='ms'
                    )
                if 'close_timestamp' in self.trades_df.columns:
                    self.trades_df['close_datetime'] = pd.to_datetime(
                        self.trades_df['close_timestamp'], unit='ms'
                    )
                
                # Calculate duration in minutes
                if 'trade_duration' in self.trades_df.columns:
                    self.trades_df['duration_minutes'] = self.trades_df['trade_duration']
                    
                print(f"Successfully processed {len(self.trades_df)} trades")
                print(f"Available columns: {list(self.trades_df.columns)}")
                
            else:
                print("No trades found in any strategy")
                self.trades_df = pd.DataFrame()
                
        except Exception as e:
            print(f"Error processing trades: {e}")
            self.trades_df = pd.DataFrame()

    def get_strategy_stats(self) -> StrategyStats:
        """Extract key strategy statistics."""
        if not self.backtest_data:
            return self._empty_stats()
        
        # More robust access to strategy data
        try:
            if 'strategy' not in self.backtest_data:
                return self._empty_stats()
            
            strategy_section = self.backtest_data['strategy']
            if not isinstance(strategy_section, dict):
                return self._empty_stats()
            
            # Get the first (and usually only) strategy
            strategy_name, strategy_data = next(iter(strategy_section.items()))
            if not isinstance(strategy_data, dict):
                return self._empty_stats()
                
            # Extract statistics directly from strategy data
            return {
                "strategy_name": strategy_name,
                "total_trades": strategy_data.get("total_trades", 0),
                "wins": strategy_data.get("wins", 0),
                "draws": strategy_data.get("draws", 0), 
                "losses": strategy_data.get("losses", 0),
                "win_rate": strategy_data.get("winrate", 0.0) * 100,  # Convert to percentage
                "total_return": strategy_data.get("profit_total", 0.0) * 100,  # Convert to percentage
                "total_return_abs": strategy_data.get("profit_total_abs", 0.0),
                "starting_balance": strategy_data.get("starting_balance", 0),
                "final_balance": strategy_data.get("final_balance", 0),
                "max_drawdown": strategy_data.get("max_drawdown_account", 0.0) * 100,  # Convert to percentage
                "max_drawdown_abs": strategy_data.get("max_drawdown_abs", 0.0),
                "sharpe_ratio": strategy_data.get("sharpe", 0.0),
                "sortino_ratio": strategy_data.get("sortino", 0.0),
                "calmar_ratio": strategy_data.get("calmar", 0.0),
                "profit_factor": strategy_data.get("profit_factor", 0.0),
                "expectancy": strategy_data.get("expectancy", 0.0),
                "sqn": strategy_data.get("sqn", 0.0),
                "backtest_start": strategy_data.get("backtest_start", "Unknown"),
                "backtest_end": strategy_data.get("backtest_end", "Unknown"),
                "backtest_days": strategy_data.get("backtest_days", 0),
                "trades_per_day": strategy_data.get("trades_per_day", 0.0),
                "avg_trade_duration": strategy_data.get("holding_avg", "Unknown"),
                "max_consecutive_wins": strategy_data.get("max_consecutive_wins", 0),
                "max_consecutive_losses": strategy_data.get("max_consecutive_losses", 0),
            }
                
        except (KeyError, IndexError, TypeError, AttributeError) as e:
            print(f"Error extracting strategy stats: {e}")
            return self._empty_stats()
    
    def _empty_stats(self) -> StrategyStats:
        """Return empty statistics dictionary."""
        return {
            "strategy_name": "Unknown",
            "total_trades": 0,
            "wins": 0,
            "draws": 0, 
            "losses": 0,
            "win_rate": 0.0,
            "total_return": 0.0,
            "total_return_abs": 0.0,
            "starting_balance": 0,
            "final_balance": 0,
            "max_drawdown": 0.0,
            "max_drawdown_abs": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "calmar_ratio": 0.0,
            "profit_factor": 0.0,
            "expectancy": 0.0,
            "sqn": 0.0,
            "backtest_start": "Unknown",
            "backtest_end": "Unknown",
            "backtest_days": 0,
            "trades_per_day": 0.0,
            "avg_trade_duration": "Unknown",
            "max_consecutive_wins": 0,
            "max_consecutive_losses": 0,
        }
    
    def create_timeline_chart(self) -> go.Figure:
        """Create a timeline chart with market data and trade signals."""
        if self.market_data is None or self.trades_df is None:
            return go.Figure().add_annotation(
                text="Market data or trade data not available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        
        # Filter market data to backtest period if possible
        if not self.trades_df.empty:
            start_time = self.trades_df['open_datetime'].min()
            end_time = self.trades_df['close_datetime'].max()
            
            # Add some buffer around the trading period
            buffer = timedelta(hours=2)
            start_time -= buffer
            end_time += buffer
            
            # Filter market data to the relevant period
            mask = (self.market_data.index >= start_time) & (self.market_data.index <= end_time)
            filtered_data = self.market_data[mask]
        else:
            filtered_data = self.market_data.head(1000)  # Show last 1000 candles if no trades
        
        if filtered_data.empty:
            return go.Figure().add_annotation(
                text="No market data in the trading period",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        
        # Create subplot with secondary y-axis for volume
        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.7, 0.3],
            subplot_titles=('Price Action with Trade Signals', 'Volume'),
            vertical_spacing=0.05,
            shared_xaxes=True
        )
        
        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=filtered_data.index,
                open=filtered_data['open'],
                high=filtered_data['high'],
                low=filtered_data['low'],
                close=filtered_data['close'],
                name='Price',
                increasing_line_color='#26a69a',
                decreasing_line_color='#ef5350'
            ),
            row=1, col=1
        )
        
        # Add volume bars
        colors = ['#26a69a' if close >= open else '#ef5350' 
                 for close, open in zip(filtered_data['close'], filtered_data['open'])]
        
        fig.add_trace(
            go.Bar(
                x=filtered_data.index,
                y=filtered_data['volume'],
                name='Volume',
                marker_color=colors,
                opacity=0.7
            ),
            row=2, col=1
        )
        
        # Add trade signals
        if not self.trades_df.empty:
            # Buy signals (trade entries)
            fig.add_trace(
                go.Scatter(
                    x=self.trades_df['open_datetime'],
                    y=self.trades_df['open_rate'],
                    mode='markers',
                    marker=dict(
                        symbol='triangle-up',
                        size=12,
                        color='#00ff00',
                        line=dict(width=2, color='#006600')
                    ),
                    name='Buy Signal',
                    hovertemplate=(
                        '<b>Buy Signal</b><br>'
                        'Time: %{x}<br>'
                        'Price: %{y:.2f}<br>'
                        'Pair: %{customdata[0]}<br>'
                        'Amount: %{customdata[1]:.6f}<br>'
                        '<extra></extra>'
                    ),
                    customdata=self.trades_df[['pair', 'amount']].values
                ),
                row=1, col=1
            )
            
            # Sell signals (trade exits)
            # Color code by exit reason
            exit_colors = {
                'custom_exit': '#ff6600',  # Orange
                'exit_signal': '#ff0000',  # Red
                'stop_loss': '#800000',    # Dark red
                'roi': '#0066ff'           # Blue
            }
            
            for exit_reason in self.trades_df['exit_reason'].unique():
                subset = self.trades_df[self.trades_df['exit_reason'] == exit_reason]
                
                fig.add_trace(
                    go.Scatter(
                        x=subset['close_datetime'],
                        y=subset['close_rate'],
                        mode='markers',
                        marker=dict(
                            symbol='triangle-down',
                            size=12,
                            color=exit_colors.get(exit_reason, '#ff0000'),
                            line=dict(width=2, color='#660000')
                        ),
                        name=f'Sell ({exit_reason})',
                        hovertemplate=(
                            f'<b>Sell Signal ({exit_reason})</b><br>'
                            'Time: %{x}<br>'
                            'Price: %{y:.2f}<br>'
                            'Profit: %{customdata[0]:.2f}%<br>'
                            'Duration: %{customdata[1]:.0f}min<br>'
                            '<extra></extra>'
                        ),
                        customdata=subset[['profit_ratio', 'duration_minutes']].values * [[100, 1]]
                    ),
                    row=1, col=1
                )
        
        # Update layout
        fig.update_layout(
            title=dict(
                text=f"Trading Timeline - {self.get_strategy_stats().get('strategy_name', 'Strategy')}",
                x=0.5,
                font=dict(size=20)
            ),
            height=800,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(t=80, b=60, l=60, r=60)
        )
        
        # Update axes
        fig.update_xaxes(
            title_text="Time",
            row=2, col=1,
            rangeslider_visible=False
        )
        
        fig.update_yaxes(
            title_text="Price (USDT)",
            row=1, col=1
        )
        
        fig.update_yaxes(
            title_text="Volume",
            row=2, col=1
        )
        
        return fig

    def create_performance_overview(self) -> Dict[str, go.Figure]:
        """Create performance overview charts."""
        figures = {}
        
        try:
            # Trade distribution chart
            if self.trades_df is not None and not self.trades_df.empty:
                wins = len(self.trades_df[self.trades_df['profit_ratio'] > 0])
                losses = len(self.trades_df[self.trades_df['profit_ratio'] < 0])
                draws = len(self.trades_df[self.trades_df['profit_ratio'] == 0])
                
                fig_dist = go.Figure(data=[
                    go.Bar(x=['Wins', 'Losses', 'Draws'], 
                           y=[wins, losses, draws],
                           marker_color=['#26a69a', '#ef5350', '#ffa726'])
                ])
                fig_dist.update_layout(
                    title="Trade Distribution",
                    xaxis_title="Trade Outcome",
                    yaxis_title="Number of Trades"
                )
                figures["trade_distribution"] = fig_dist
                
                # Pair profitability chart  
                if 'pair' in self.trades_df.columns:
                    pair_profits = self.trades_df.groupby('pair')['profit_ratio'].sum() * 100
                    
                    fig_profit = go.Figure(data=[
                        go.Bar(x=pair_profits.index, 
                               y=pair_profits.values,
                               marker_color=['#26a69a' if x > 0 else '#ef5350' for x in pair_profits.values])
                    ])
                    fig_profit.update_layout(
                        title="Profit by Trading Pair",
                        xaxis_title="Trading Pair",
                        yaxis_title="Profit (%)"
                    )
                    figures["pair_profit"] = fig_profit
                    
                    # Pair win rate chart
                    pair_stats = self.trades_df.groupby('pair').agg({
                        'profit_ratio': lambda x: (x > 0).mean() * 100
                    }).round(2)
                    
                    fig_winrate = go.Figure(data=[
                        go.Bar(x=pair_stats.index, 
                               y=pair_stats['profit_ratio'],
                               marker_color='#42a5f5')
                    ])
                    fig_winrate.update_layout(
                        title="Win Rate by Trading Pair",
                        xaxis_title="Trading Pair", 
                        yaxis_title="Win Rate (%)"
                    )
                    figures["pair_winrate"] = fig_winrate
            else:
                # Create empty charts when no trade data is available
                empty_fig = go.Figure()
                empty_fig.add_annotation(
                    text="No trade data available",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False
                )
                empty_fig.update_layout(title="No Data Available")
                
                figures["trade_distribution"] = empty_fig
                figures["pair_profit"] = empty_fig
                figures["pair_winrate"] = empty_fig
                
        except Exception as e:
            print(f"Error creating performance overview: {e}")
            # Create error chart
            error_fig = go.Figure()
            error_fig.add_annotation(
                text=f"Error creating charts: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            error_fig.update_layout(title="Chart Creation Error")
            
            figures["trade_distribution"] = error_fig
            figures["pair_profit"] = error_fig  
            figures["pair_winrate"] = error_fig
                
        return figures
    
    def create_trade_analysis(self) -> Dict[str, go.Figure]:
        """Create detailed trade analysis charts."""
        figures = {}
        
        try:
            if self.trades_df is None or self.trades_df.empty:
                # Create empty charts when no trade data is available
                empty_fig = go.Figure()
                empty_fig.add_annotation(
                    text="No trade data available",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False
                )
                empty_fig.update_layout(title="No Data Available")
                
                figures["exit_reasons"] = empty_fig
                figures["duration"] = empty_fig
                figures["profit_distribution"] = empty_fig
                
                return figures
            
            # Exit reasons analysis
            if 'exit_reason' in self.trades_df.columns:
                exit_counts = self.trades_df['exit_reason'].value_counts()
                
                fig_exit = go.Figure(data=[
                    go.Pie(labels=exit_counts.index, 
                           values=exit_counts.values,
                           hole=0.4)
                ])
                fig_exit.update_layout(title="Exit Reasons Distribution")
                figures["exit_reasons"] = fig_exit
            else:
                figures["exit_reasons"] = self._create_no_data_chart("Exit Reasons - No Data")
            
            # Duration analysis
            if 'duration_minutes' in self.trades_df.columns:
                profitable_trades = self.trades_df[self.trades_df['profit_ratio'] > 0]['duration_minutes']
                losing_trades = self.trades_df[self.trades_df['profit_ratio'] < 0]['duration_minutes']
                
                fig_duration = go.Figure()
                
                if not profitable_trades.empty:
                    fig_duration.add_trace(go.Histogram(
                        x=profitable_trades,
                        name='Profitable Trades',
                        marker_color='#26a69a',
                        opacity=0.7
                    ))
                
                if not losing_trades.empty:
                    fig_duration.add_trace(go.Histogram(
                        x=losing_trades,
                        name='Losing Trades', 
                        marker_color='#ef5350',
                        opacity=0.7
                    ))
                
                fig_duration.update_layout(
                    title="Trade Duration Distribution",
                    xaxis_title="Duration (minutes)",
                    yaxis_title="Number of Trades",
                    barmode='overlay'
                )
                figures["duration"] = fig_duration
            else:
                figures["duration"] = self._create_no_data_chart("Duration Analysis - No Data")
            
            # Profit distribution
            if 'profit_ratio' in self.trades_df.columns:
                profit_pct = self.trades_df['profit_ratio'] * 100
                
                fig_profit_dist = go.Figure()
                fig_profit_dist.add_trace(go.Histogram(
                    x=profit_pct,
                    nbinsx=20,
                    marker_color='#42a5f5',
                    opacity=0.7
                ))
                fig_profit_dist.update_layout(
                    title="Profit Distribution",
                    xaxis_title="Profit (%)",
                    yaxis_title="Number of Trades"
                )
                figures["profit_distribution"] = fig_profit_dist
            else:
                figures["profit_distribution"] = self._create_no_data_chart("Profit Distribution - No Data")
                
        except Exception as e:
            print(f"Error creating trade analysis: {e}")
            # Create error chart
            error_fig = self._create_error_chart(f"Error creating trade analysis: {str(e)}")
            
            figures["exit_reasons"] = error_fig
            figures["duration"] = error_fig
            figures["profit_distribution"] = error_fig
        
        return figures
    
    def _create_no_data_chart(self, title: str) -> go.Figure:
        """Create a chart for when no data is available."""
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        fig.update_layout(title=title)
        return fig
    
    def _create_error_chart(self, message: str) -> go.Figure:
        """Create a chart for when there's an error."""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        fig.update_layout(title="Error")
        return fig


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="FreqTrade Backtest Analyzer",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .big-font {
        font-size: 2rem !important;
        font-weight: bold;
    }
    .medium-font {
        font-size: 1.2rem !important;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize analyzer
    analyzer = BacktestAnalyzer()
    
    # Header
    st.title("📊 FreqTrade Backtest Analyzer")
    st.markdown("Technical analysis dashboard for Multi-Horizon Momentum Strategy results")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📁 Backtest Selection")
        
        # File selector
        backtest_dir = Path("user_data/backtest_results")
        if backtest_dir.exists():
            backtest_files = list(backtest_dir.glob("*.zip")) + list(backtest_dir.glob("*.json"))
            if backtest_files:
                # Sort files by modification time (most recent first)
                backtest_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                selected_file = st.selectbox(
                    "Select backtest result:",
                    backtest_files,
                    format_func=lambda x: x.name,
                    index=0  # Default to most recent file
                )
                
                if st.button("Load Backtest", type="primary"):
                    if analyzer.load_backtest_file(selected_file):
                        st.success("✅ Backtest loaded successfully!")
                        
                        # Try to load market data for the first pair
                        stats = analyzer.get_strategy_stats()
                        if analyzer.trades_df is not None and not analyzer.trades_df.empty:
                            first_pair = analyzer.trades_df['pair'].iloc[0]
                            timeframe = stats.get('timeframe', '1m')
                            if analyzer.load_market_data(first_pair, timeframe):
                                st.success(f"✅ Market data loaded for {first_pair}")
                            else:
                                st.warning(f"⚠️ Could not load market data for {first_pair}")
                    else:
                        st.error("❌ Failed to load backtest")
            else:
                st.warning("No backtest files found in user_data/backtest_results/")
        else:
            st.error("Backtest results directory not found!")
    
    # Main content
    if analyzer.backtest_data:
        stats = analyzer.get_strategy_stats()
        
        # Strategy info
        if stats:
            st.markdown("### 📋 Quick Stats")
            st.markdown(f"**Strategy:** {stats.get('strategy_name', 'Unknown')}")  
            st.markdown(f"**Timeframe:** {stats.get('timeframe', 'Unknown')}")
            st.markdown(f"**Backtest Period:** {stats.get('backtest_days', 0)} days")
            
            # Main metrics in columns
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Trades", stats.get('total_trades', 0))
            with col2:
                st.metric("Win Rate", f"{stats.get('win_rate', 0):.2f}%")
            with col3:
                st.metric("Total Return", f"{stats.get('total_return', 0):.2f}%")
            with col4:
                st.metric("Max Drawdown", f"{stats.get('max_drawdown', 0):.2f}%")
            
            col5, col6, col7, col8 = st.columns(4)
            with col5:
                st.metric("Sharpe Ratio", f"{stats.get('sharpe_ratio', 0):.2f}")
            with col6:
                st.metric("Profit Factor", f"{stats.get('profit_factor', 0):.2f}")
            with col7:
                st.metric("Expectancy", f"{stats.get('expectancy', 0):.4f}")
            with col8:
                st.metric("Starting Balance", f"{stats.get('starting_balance', 0)} USDT")
        else:
            st.error("No backtest data loaded")
            st.markdown("**Strategy:** Unknown")
            st.markdown("**Timeframe:** Unknown") 
            st.markdown("**Backtest Period:** 0 days")
        
        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Overview", 
            "📊 Trade Analysis", 
            "⚠️ Risk Metrics", 
            "🧠 Insights"
        ])
        
        with tab1:
            st.subheader("Performance Overview")
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Trades", stats.get('total_trades', 0))
            with col2:
                st.metric("Win Rate", f"{stats.get('win_rate', 0):.2f}%")
            with col3:
                st.metric("Total Return", f"{stats.get('total_return', 0):.2f}%")
            with col4:
                st.metric("Max Drawdown", f"{stats.get('max_drawdown', 0):.2f}%")
            
            col5, col6, col7, col8 = st.columns(4)
            with col5:
                st.metric("Sharpe Ratio", f"{stats.get('sharpe_ratio', 0):.2f}")
            with col6:
                st.metric("CAGR", f"{stats.get('cagr', 0):.2f}%")
            with col7:
                st.metric("Expectancy", f"{stats.get('expectancy', 0):.4f}")
            with col8:
                st.metric("Profit Factor", f"{stats.get('profit_factor', 0):.2f}")
            
            # Performance charts
            perf_figures = analyzer.create_performance_overview()
            
            # Display performance charts
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📊 Trade Distribution")
                st.plotly_chart(perf_figures["trade_distribution"], use_container_width=True, key="trade_distribution_chart")
            
            with col2:
                st.subheader("💰 Pair Profitability")
                st.plotly_chart(perf_figures["pair_profit"], use_container_width=True, key="pair_profit_chart_1")
            
            # Pair performance breakdown
            st.subheader("🎯 Detailed Pair Performance")
            col3, col4 = st.columns(2)
            with col3:
                st.plotly_chart(perf_figures["pair_profit"], use_container_width=True, key="pair_profit_chart_2")
            with col4:
                st.plotly_chart(perf_figures["pair_winrate"], use_container_width=True, key="pair_winrate_chart")
        
        with tab2:  # Trade Analysis
            st.header("📈 Market Timeline & Trade Analysis")
            
            # Timeline Chart
            st.subheader("🕐 Trading Timeline")
            st.info("📊 Interactive chart showing market data with buy/sell signals overlaid")
            
            timeline_fig = analyzer.create_timeline_chart()
            st.plotly_chart(timeline_fig, use_container_width=True, key="timeline_chart")
            
            # Get trade analysis figures
            trade_figures = analyzer.create_trade_analysis()
            
            st.subheader("📊 Trade Analysis")
            
            # Trade analysis charts
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🚪 Exit Reasons")
                st.plotly_chart(trade_figures["exit_reasons"], use_container_width=True, key="exit_reasons_chart")
                
            with col2:
                st.subheader("⏱️ Trade Duration Analysis")
                st.plotly_chart(trade_figures["duration"], use_container_width=True, key="duration_chart")
            
            st.subheader("💰 Profit Distribution")
            st.plotly_chart(trade_figures["profit_distribution"], use_container_width=True, key="profit_distribution_chart")
        
        with tab3:
            st.subheader("⚠️ Risk Management Analysis")
            
            # Risk metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Max Drawdown", f"{stats.get('max_drawdown_abs', 0):.4f} USDT")
            with col2:
                st.metric("Max Drawdown %", f"{stats.get('max_drawdown', 0):.2f}%")
            with col3:
                sharpe = stats.get('sharpe_ratio', 0)
                sharpe_color = "green" if sharpe > 1 else "orange" if sharpe > 0 else "red"
                st.markdown(f"**Sharpe Ratio:** <span style='color: {sharpe_color}'>{sharpe:.2f}</span>", 
                           unsafe_allow_html=True)
            
            # Risk insights
            st.markdown("### Risk Assessment")
            sharpe = stats.get('sharpe_ratio', 0)
            win_rate = stats.get('win_rate', 0)
            profit_factor = stats.get('profit_factor', 0)
            
            if sharpe < -1:
                st.error("🔴 **High Risk**: Very poor risk-adjusted returns")
            elif sharpe < 0:
                st.warning("🟡 **Medium Risk**: Negative risk-adjusted returns")
            elif sharpe < 1:
                st.info("🔵 **Moderate Risk**: Below-average risk-adjusted returns")
            else:
                st.success("🟢 **Lower Risk**: Good risk-adjusted returns")
        
        with tab4:
            st.subheader("🧠 AI-Powered Strategy Insights")
            
            # Performance insights
            total_trades = stats.get('total_trades', 0)
            win_rate = stats.get('win_rate', 0)
            profit_factor = stats.get('profit_factor', 0)
            expectancy = stats.get('expectancy', 0)
            
            insights = []
            
            if total_trades < 30:
                insights.append("⚠️ **Sample Size**: Consider running longer backtests (>100 trades) for statistical significance")
            
            if win_rate < 40:
                insights.append("🎯 **Win Rate**: Low win rate suggests need for better entry criteria or tighter filters")
                
            if profit_factor < 1.0:
                insights.append("💰 **Profit Factor**: Strategy is losing money - review exit conditions and risk management")
            elif profit_factor > 2.0:
                insights.append("✅ **Profit Factor**: Excellent profit factor indicates good strategy performance")
                
            if expectancy < 0:
                insights.append("📉 **Expectancy**: Negative expectancy means average trade loses money")
            elif expectancy > 0.01:
                insights.append("📈 **Expectancy**: Positive expectancy shows profitable edge")
            
            # Multi-Horizon Momentum specific insights
            if analyzer.trades_df is not None and not analyzer.trades_df.empty:
                avg_duration = analyzer.trades_df['duration_minutes'].mean()
                if avg_duration < 5:
                    insights.append("⚡ **Duration**: Very short trades suggest scalping approach - ensure low slippage")
                elif avg_duration > 60:
                    insights.append("🕒 **Duration**: Longer hold times - consider overnight gap risk")
                
                # Exit reason analysis
                exit_reasons = analyzer.trades_df['exit_reason'].value_counts()
                custom_exit_pct = (exit_reasons.get('custom_exit', 0) / total_trades) * 100
                if custom_exit_pct > 70:
                    insights.append("🎯 **Exit Strategy**: High custom_exit usage suggests ATR-based exits working well")
            
            if insights:
                for insight in insights:
                    st.markdown(insight)
            else:
                st.info("📊 Run more trades to generate detailed insights")
            
            # Strategy-specific recommendations
            st.markdown("### 🔧 Optimization Recommendations")
            
            recs = []
            if win_rate < 45:
                recs.append("• **Tighten entry filters**: Increase RSI threshold or add volume confirmation")
                recs.append("• **Improve market timing**: Consider additional timeframe confirmations")
                
            if profit_factor < 1.5:
                recs.append("• **Review ATR multipliers**: Test different TP/SL ratios")
                recs.append("• **Exit optimization**: Analyze if trailing stops are too tight")
                
            recs.append("• **Pair diversification**: Test strategy on additional crypto pairs")
            recs.append("• **Market condition analysis**: Check performance in different volatility regimes")
            
            for rec in recs:
                st.markdown(rec)
                
    else:
        # Landing page
        st.markdown("""
        ## Welcome to the FreqTrade Backtest Analyzer! 🚀
        
        This dashboard provides comprehensive analysis of your Multi-Horizon Momentum Strategy results.
        
        ### 📊 Features:
        - **Performance Overview**: Key metrics, win rates, and profitability analysis
        - **Trade Analysis**: Detailed breakdown of trade patterns and behaviors  
        - **Timeline Chart**: Visualize market data with buy/sell signals overlaid
        - **Risk Metrics**: Drawdown analysis and risk-adjusted returns
        - **AI Insights**: Strategy-specific recommendations and optimizations
        
        ### 🚀 Getting Started:
        1. Select a backtest result file from the sidebar
        2. Click "Load Backtest" to analyze your results
        3. Explore the different tabs for detailed insights
        
        ### 📈 Timeline Feature:
        The timeline chart shows your actual trades overlaid on market candlestick data:
        - **Green triangles**: Entry signals
        - **Red/Orange triangles**: Exit signals (color-coded by exit reason)
        - **Candlesticks**: Market price action
        - **Volume bars**: Trading volume
        """)


if __name__ == "__main__":
    main() 