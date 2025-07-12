#!/usr/bin/env python3
"""
Runner script for the FreqTrade Backtest Analyzer
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Run the Streamlit dashboard."""
    analyzer_path = Path("backtest_analyzer.py")
    
    if not analyzer_path.exists():
        print("❌ backtest_analyzer.py not found!")
        return
    
    print("🚀 Starting FreqTrade Backtest Analyzer...")
    print("📊 Dashboard will open in your browser at http://localhost:8501")
    print("🛑 Press Ctrl+C to stop the server")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(analyzer_path),
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n✅ Dashboard stopped.")

if __name__ == "__main__":
    main() 