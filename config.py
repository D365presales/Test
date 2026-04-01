"""
Configuration for crypto backtesting framework.
"""

# Trading pairs (ccxt format)
PAIRS = [
    "BTC/USD",
    "ETH/USD",
    "SOL/USD",
]

# Timeframe
TIMEFRAME = "4h"

# Backtest period (1 year of historical data)
LOOKBACK_DAYS = 365

# Exchange to fetch data from
EXCHANGE = "kraken"

# Initial capital in CAD
INITIAL_CAPITAL = 1000.0
CURRENCY = "CAD"

# Entry style
LONG_ONLY = True
USE_LEVERAGE = False

# Position sizing: 100% of available capital per trade
POSITION_SIZE_PCT = 1.0

# Strategy parameters
SMA_FAST = 20
SMA_SLOW = 200

# Two-Pole Oscillator parameters (BigBeluga style)
TWO_POLE_LENGTH = 20
TWO_POLE_SMA_LENGTH = 25
TWO_POLE_LOOKBACK = 4  # Signal comparison offset

# Volume filter parameters
VOLUME_MULTIPLIER = 1.5
VOLUME_PERIOD = 20

# Runs directory (each backtest gets a dated subfolder)
RUNS_DIR = "runs"

# Master stats CSV (all runs aggregated)
MASTER_STATS_FILE = "results/master_stats.csv"

# Legacy compatibility (used by run_all.py to set per-run paths)
DATA_DIR = "data"
RESULTS_DIR = "results"
RESULTS_FILE = "results/stats.csv"
