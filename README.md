# Crypto & Stock Backtesting Framework

A Python backtesting framework for crypto and stock trading strategies. Built for **LONG ONLY spot trading** with no leverage.

## Configuration

| Setting | Value |
|---------|-------|
| Pairs | BTC/USD, ETH/USD, SOL/USD (crypto) — stocks supported via yfinance |
| Timeframe | 4H candles |
| Backtest Period | 1 year |
| Initial Capital | $1,000 CAD |
| Entry Style | LONG ONLY (spot) |
| Data Sources | Kraken/Binance (crypto via ccxt), yfinance (stocks) |

## Strategies

### 1. SMA 20/200 Crossover
Classic golden cross / death cross. Long when SMA20 crosses above SMA200, exit when SMA20 crosses below.

### 2. Two-Pole Oscillator (BigBeluga)
Based on [BigBeluga's TradingView indicator](https://www.tradingview.com/script/2Ssn4yDZ-Two-Pole-Oscillator-BigBeluga/). Uses a two-pole Butterworth-style filter on price deviation. Buy on oversold crossover, sell on overbought crossover.

### 3. Volume Filter
Trend-following with volume confirmation. Entry requires price above SMA(20) AND volume > 1.5x the 20-period average.

### 4. Combined Strategy
All three indicators as confluence. Entry requires SMA bullish regime + oscillator buy signal + volume confirmation.

## Project Structure

```
├── README.md               # this file
├── requirements.txt        # Python dependencies
├── config.py               # pairs, timeframes, settings
├── strategies/             # reusable strategy implementations
│   ├── sma_crossover.py
│   ├── two_pole_oscillator.py
│   ├── volume_filter.py
│   └── combined.py
├── pinescript/             # original PineScript source files
│   └── two_pole_oscillator.pine
├── backtests/              # backtest runner scripts
│   └── run_all.py          # main entry point
├── utils/
│   ├── data_fetcher.py     # OHLCV data download (ccxt + yfinance)
│   └── stats_logger.py     # CSV logging (run + master stats)
├── runs/                   # each backtest gets a dated folder
│   └── YYYY-MM-DD_type_tf/ # auto-created per run
│       ├── data/           # OHLCV CSVs for this run
│       ├── results/        # stats.csv for this run
│       └── README.md       # auto-generated summary
├── results/
│   └── master_stats.csv    # ALL runs aggregated — one big sortable file
└── .gitignore
```

## Setup

```bash
pip install -r requirements.txt
```

## Usage

### Run all backtests (creates a new dated run folder automatically):
```bash
cd backtests
python run_all.py
```

Each run:
1. Creates a folder under `runs/` named `YYYY-MM-DD_crypto_4h` (or `stocks`, `mixed`)
2. Fetches and saves OHLCV data to `runs/<run>/data/`
3. Runs all strategies and saves results to `runs/<run>/results/stats.csv`
4. Appends results to `results/master_stats.csv` for cross-run comparison
5. Generates a `runs/<run>/README.md` summary with key metrics

### Fetch data only:
```bash
python -m utils.data_fetcher
```

### Stock support:
Add stock tickers to `config.py` PAIRS list. Supported formats:
- `AAPL` — plain ticker (auto-detected as stock)
- `NASDAQ:AAPL` — exchange-prefixed
- `TSX:SHOP` — Canadian stocks (auto-converts to SHOP.TO for yfinance)

## Master Stats

The `results/master_stats.csv` file aggregates all runs with columns:
- `run` — the run folder name (date + asset type + timeframe)
- `strategy_name`, `pair`, `roi`, `drawdown`, `sharpe`, `sortino`, `win_rate`, `num_trades`, `expected_value`

Sort/filter to compare strategies across different time periods and market conditions.

## Adding New Strategies

1. Create a new file in `strategies/`
2. Implement a class extending `backtesting.Strategy`
3. Add it to `STRATEGIES` dict in `backtests/run_all.py`
4. Run the backtests

## Disclaimer

This is for educational and research purposes only. Not financial advice. Past performance does not guarantee future results. Always do your own research and manage risk appropriately.
