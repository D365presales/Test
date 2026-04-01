"""
Backtest runner — runs all strategies against all pairs and generates stats.csv.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from backtesting import Backtest
from backtesting.lib import FractionalBacktest
from utils.data_fetcher import fetch_all, load_data, fetch_ohlcv, save_data
from utils.stats_logger import calculate_stats, log_stats, format_stats_comment
from strategies.sma_crossover import SMACrossover
from strategies.two_pole_oscillator import TwoPoleOscillator
from strategies.volume_filter import VolumeFilter
from strategies.combined import CombinedStrategy


STRATEGIES = {
    "SMA_20_200_Crossover": SMACrossover,
    "Two_Pole_Oscillator": TwoPoleOscillator,
    "Volume_Filter": VolumeFilter,
    "Combined_Strategy": CombinedStrategy,
}


def ensure_data():
    """Fetch data if not cached."""
    for pair in config.PAIRS:
        filename = pair.replace("/", "_") + f"_{config.TIMEFRAME}.csv"
        filepath = os.path.join(config.DATA_DIR, filename)
        if not os.path.exists(filepath):
            print(f"Data for {pair} not found, fetching...")
            df = fetch_ohlcv(pair)
            save_data(df, pair)
        else:
            print(f"Using cached data for {pair}")


def run_backtest(strategy_class, strategy_name: str, pair: str, data) -> dict:
    """Run a single backtest and return stats dict."""
    print(f"\n{'='*60}")
    print(f"Running: {strategy_name} on {pair}")
    print(f"{'='*60}")

    bt = FractionalBacktest(
        data,
        strategy_class,
        cash=config.INITIAL_CAPITAL,
        commission=0.001,  # 0.1% typical exchange fee
        exclusive_orders=True,
        trade_on_close=True,
    )

    stats = bt.run()

    result = calculate_stats(stats, strategy_name, pair)

    print(f"  ROI: {result['roi']}%")
    print(f"  Max Drawdown: {result['drawdown']}%")
    print(f"  Sharpe: {result['sharpe']}")
    print(f"  Sortino: {result['sortino']}")
    print(f"  Win Rate: {result['win_rate']}%")
    print(f"  Trades: {result['num_trades']}")
    print(f"  EV/Trade: ${result['expected_value']}")

    return result


def update_strategy_file_comments(results: list[dict]):
    """Write stats as comments at the top of each strategy file."""
    strategy_file_map = {
        "SMA_20_200_Crossover": "strategies/sma_crossover.py",
        "Two_Pole_Oscillator": "strategies/two_pole_oscillator.py",
        "Volume_Filter": "strategies/volume_filter.py",
        "Combined_Strategy": "strategies/combined.py",
    }

    # Group results by strategy
    grouped = {}
    for r in results:
        name = r["strategy_name"]
        if name not in grouped:
            grouped[name] = []
        grouped[name].append(r)

    for strategy_name, filepath in strategy_file_map.items():
        full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), filepath)
        if not os.path.exists(full_path):
            continue

        with open(full_path, "r") as f:
            content = f.read()

        # Remove existing stats comments (between markers)
        marker = "# ============================================================"
        while marker in content:
            start = content.find(marker)
            # Find the closing marker
            end = content.find(marker, start + len(marker))
            if end != -1:
                end += len(marker)
                # Remove trailing newline
                if end < len(content) and content[end] == "\n":
                    end += 1
                content = content[:start] + content[end:]
            else:
                break

        # Build stats header
        stats_lines = []
        if strategy_name in grouped:
            for r in grouped[strategy_name]:
                stats_lines.append(format_stats_comment(r))

        if stats_lines:
            header = "\n".join(stats_lines) + "\n"
            content = header + content

        with open(full_path, "w") as f:
            f.write(content)

        print(f"Updated {filepath} with stats comments")


def main():
    print("=" * 60)
    print("CRYPTO BACKTESTING FRAMEWORK")
    print(f"Capital: ${config.INITIAL_CAPITAL} {config.CURRENCY}")
    print(f"Pairs: {', '.join(config.PAIRS)}")
    print(f"Timeframe: {config.TIMEFRAME}")
    print(f"Mode: LONG ONLY / Spot / No leverage")
    print("=" * 60)

    # Ensure data is available
    ensure_data()

    all_results = []

    for pair in config.PAIRS:
        data = load_data(pair)

        for strategy_name, strategy_class in STRATEGIES.items():
            try:
                result = run_backtest(strategy_class, strategy_name, pair, data)
                all_results.append(result)
            except Exception as e:
                print(f"\n  ERROR running {strategy_name} on {pair}: {e}")
                import traceback
                traceback.print_exc()
                all_results.append({
                    "strategy_name": strategy_name,
                    "pair": pair,
                    "roi": 0, "drawdown": 0, "sharpe": 0,
                    "sortino": 0, "win_rate": 0, "num_trades": 0,
                    "expected_value": 0,
                })

    # Save stats
    log_stats(all_results)

    # Update strategy files with stats comments
    update_strategy_file_comments(all_results)

    # Print summary table
    print("\n" + "=" * 90)
    print(f"{'Strategy':<25} {'Pair':<10} {'ROI%':>8} {'DD%':>8} {'Sharpe':>8} {'WR%':>8} {'Trades':>8}")
    print("-" * 90)
    for r in all_results:
        print(f"{r['strategy_name']:<25} {r['pair']:<10} {r['roi']:>7.1f}% {r['drawdown']:>7.1f}% {r['sharpe']:>8.2f} {r['win_rate']:>7.1f}% {r['num_trades']:>8}")
    print("=" * 90)


if __name__ == "__main__":
    main()
