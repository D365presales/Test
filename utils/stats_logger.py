"""
Stats logger — calculates and saves backtest statistics to CSV.
Supports writing to both run-specific folder AND master_stats.csv.
"""

import os
import csv
import numpy as np
import pandas as pd

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

FIELDNAMES = [
    "strategy_name", "pair", "roi", "drawdown", "sharpe",
    "sortino", "win_rate", "num_trades", "expected_value"
]

MASTER_FIELDNAMES = ["run"] + FIELDNAMES


def calculate_stats(stats, strategy_name: str, pair: str) -> dict:
    """
    Extract stats from backtesting.py Stats object.
    Returns a dict with all required metrics.
    """
    equity_curve = stats["_equity_curve"]
    equity = equity_curve["Equity"]

    # Calculate returns
    returns = equity.pct_change().dropna()

    # ROI
    roi = ((equity.iloc[-1] - equity.iloc[0]) / equity.iloc[0]) * 100

    # Max Drawdown
    drawdown = stats.get("Max. Drawdown [%]", 0)
    if drawdown is None or (isinstance(drawdown, float) and np.isnan(drawdown)):
        drawdown = 0.0

    # Sharpe Ratio (annualized, assuming 4H candles = 6 per day = ~2190 per year)
    periods_per_year = 365.25 * 24 / 4  # ~2191.5
    if len(returns) > 1 and returns.std() > 0:
        sharpe = (returns.mean() / returns.std()) * np.sqrt(periods_per_year)
    else:
        sharpe = 0.0

    # Sortino Ratio
    downside_returns = returns[returns < 0]
    if len(downside_returns) > 1 and downside_returns.std() > 0:
        sortino = (returns.mean() / downside_returns.std()) * np.sqrt(periods_per_year)
    else:
        sortino = 0.0

    # Win Rate
    win_rate = stats.get("Win Rate [%]", 0)
    if win_rate is None or (isinstance(win_rate, float) and np.isnan(win_rate)):
        win_rate = 0.0

    # Number of trades
    num_trades = stats.get("# Trades", 0)

    # Expected Value per trade
    if num_trades > 0:
        total_return = equity.iloc[-1] - equity.iloc[0]
        expected_value = total_return / num_trades
    else:
        expected_value = 0.0

    return {
        "strategy_name": strategy_name,
        "pair": pair,
        "roi": round(roi, 2),
        "drawdown": round(abs(drawdown), 2),
        "sharpe": round(sharpe, 4),
        "sortino": round(sortino, 4),
        "win_rate": round(win_rate, 2),
        "num_trades": int(num_trades),
        "expected_value": round(expected_value, 2),
    }


def log_stats(results: list[dict], results_dir: str = None, results_file: str = None):
    """
    Write all results to stats.csv in the specified directory.
    Falls back to config defaults if not provided.
    """
    results_dir = results_dir or config.RESULTS_DIR
    results_file = results_file or os.path.join(results_dir, "stats.csv")

    os.makedirs(os.path.dirname(results_file), exist_ok=True)

    with open(results_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nStats saved to {results_file}")


def append_to_master(results: list[dict], run_name: str, master_file: str = None):
    """
    Append results to the master_stats.csv with a run identifier column.
    Creates the file with headers if it doesn't exist.
    """
    master_file = master_file or config.MASTER_STATS_FILE
    os.makedirs(os.path.dirname(master_file), exist_ok=True)

    file_exists = os.path.exists(master_file) and os.path.getsize(master_file) > 0

    with open(master_file, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MASTER_FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        for row in results:
            master_row = {"run": run_name, **row}
            writer.writerow(master_row)

    print(f"Appended {len(results)} rows to {master_file}")


def format_stats_comment(result: dict) -> str:
    """Format a stats dict as a Python comment block for file headers."""
    lines = [
        "# ============================================================",
        f"# Strategy: {result['strategy_name']}",
        f"# Pair: {result['pair']}",
        f"# ROI: {result['roi']}%",
        f"# Max Drawdown: {result['drawdown']}%",
        f"# Sharpe Ratio: {result['sharpe']}",
        f"# Sortino Ratio: {result['sortino']}",
        f"# Win Rate: {result['win_rate']}%",
        f"# Number of Trades: {result['num_trades']}",
        f"# Expected Value/Trade: ${result['expected_value']}",
        "# ============================================================",
    ]
    return "\n".join(lines)
