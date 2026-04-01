"""
Backtest runner — runs all strategies against all pairs and generates stats.csv.
Auto-creates a dated run folder and saves data + results there.
Also appends to the master_stats.csv for cross-run comparison.
"""

import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from backtesting import Backtest
from backtesting.lib import FractionalBacktest
from utils.data_fetcher import fetch_all, load_data, fetch_ohlcv, save_data
from utils.stats_logger import calculate_stats, log_stats, append_to_master, format_stats_comment
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


def create_run_folder() -> tuple[str, str]:
    """
    Create a dated run folder under runs/.
    Format: YYYY-MM-DD_symbols_timeframe
    Returns (run_name, run_dir_path).
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    date_str = datetime.now().strftime("%Y-%m-%d")

    # Build symbol descriptor from config
    symbols = []
    has_crypto = False
    has_stocks = False
    for pair in config.PAIRS:
        if "/" in pair:
            has_crypto = True
        else:
            has_stocks = True

    if has_crypto and has_stocks:
        asset_type = "mixed"
    elif has_stocks:
        asset_type = "stocks"
    else:
        asset_type = "crypto"

    run_name = f"{date_str}_{asset_type}_{config.TIMEFRAME}"

    # Handle duplicate run names (add suffix)
    run_dir = os.path.join(project_root, config.RUNS_DIR, run_name)
    if os.path.exists(run_dir):
        counter = 2
        while os.path.exists(f"{run_dir}_{counter}"):
            counter += 1
        run_name = f"{run_name}_{counter}"
        run_dir = os.path.join(project_root, config.RUNS_DIR, run_name)

    os.makedirs(os.path.join(run_dir, "data"), exist_ok=True)
    os.makedirs(os.path.join(run_dir, "results"), exist_ok=True)

    print(f"\nRun folder: {run_dir}")
    return run_name, run_dir


def generate_run_readme(run_dir: str, run_name: str, all_results: list[dict]):
    """Generate a README.md summary for the run folder."""
    readme_path = os.path.join(run_dir, "README.md")

    lines = [
        f"# Run: {run_name}",
        "",
        "## Configuration",
        f"- **Pairs:** {', '.join(config.PAIRS)}",
        f"- **Timeframe:** {config.TIMEFRAME}",
        f"- **Initial Capital:** ${config.INITIAL_CAPITAL} {config.CURRENCY}",
        f"- **Mode:** LONG ONLY / Spot / No leverage",
        f"- **Run Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Results",
        "",
        "| Strategy | Pair | ROI% | Max DD% | Sharpe | Win Rate% | Trades | EV/Trade |",
        "|----------|------|------|---------|--------|-----------|--------|----------|",
    ]

    for r in all_results:
        lines.append(
            f"| {r['strategy_name']} | {r['pair']} | {r['roi']} | {r['drawdown']} "
            f"| {r['sharpe']} | {r['win_rate']} | {r['num_trades']} | ${r['expected_value']} |"
        )

    # Find best/worst
    if all_results:
        best = max(all_results, key=lambda x: x["roi"])
        worst = min(all_results, key=lambda x: x["roi"])
        lowest_dd = min(all_results, key=lambda x: x["drawdown"])

        lines.extend([
            "",
            "## Highlights",
            f"- **Best ROI:** {best['strategy_name']} on {best['pair']} ({best['roi']}%)",
            f"- **Worst ROI:** {worst['strategy_name']} on {worst['pair']} ({worst['roi']}%)",
            f"- **Lowest Drawdown:** {lowest_dd['strategy_name']} on {lowest_dd['pair']} ({lowest_dd['drawdown']}%)",
        ])

    with open(readme_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Run README saved to {readme_path}")


def ensure_data(data_dir: str):
    """Fetch data if not cached, saving to run-specific data dir."""
    for pair in config.PAIRS:
        clean_pair = pair.replace("/", "_").replace(":", "_")
        filename = clean_pair + f"_{config.TIMEFRAME}.csv"
        filepath = os.path.join(data_dir, filename)
        if not os.path.exists(filepath):
            print(f"Fetching data for {pair}...")
            df = fetch_ohlcv(pair)
            save_data(df, pair, data_dir)
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

    # Create run folder
    run_name, run_dir = create_run_folder()
    data_dir = os.path.join(run_dir, "data")
    results_dir = os.path.join(run_dir, "results")
    results_file = os.path.join(results_dir, "stats.csv")

    # Ensure data is available in the run folder
    ensure_data(data_dir)

    all_results = []

    for pair in config.PAIRS:
        data = load_data(pair, data_dir)

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

    # Save stats to run folder
    log_stats(all_results, results_dir, results_file)

    # Append to master stats
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    master_file = os.path.join(project_root, config.MASTER_STATS_FILE)
    append_to_master(all_results, run_name, master_file)

    # Generate run README
    generate_run_readme(run_dir, run_name, all_results)

    # Update strategy files with stats comments
    update_strategy_file_comments(all_results)

    # Print summary table
    print("\n" + "=" * 90)
    print(f"{'Strategy':<25} {'Pair':<10} {'ROI%':>8} {'DD%':>8} {'Sharpe':>8} {'WR%':>8} {'Trades':>8}")
    print("-" * 90)
    for r in all_results:
        print(f"{r['strategy_name']:<25} {r['pair']:<10} {r['roi']:>7.1f}% {r['drawdown']:>7.1f}% {r['sharpe']:>8.2f} {r['win_rate']:>7.1f}% {r['num_trades']:>8}")
    print("=" * 90)
    print(f"\nResults saved to: {run_dir}")
    print(f"Master stats: {master_file}")


if __name__ == "__main__":
    main()
