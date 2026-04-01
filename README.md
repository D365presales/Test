# Crypto Backtesting Framework

A Python backtesting framework for crypto trading strategies. Built for **LONG ONLY spot trading** with no leverage.

## Configuration

| Setting | Value |
|---------|-------|
| Pairs | BTC/USD, ETH/USD, SOL/USD |
| Timeframe | 4H candles |
| Backtest Period | 1 year |
| Initial Capital | $1,000 CAD |
| Entry Style | LONG ONLY (spot) |
| Data Source | Kraken (via ccxt) |

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
├── README.md
├── requirements.txt
├── config.py              # pairs, timeframes, settings
├── data/                  # cached OHLCV data
├── pinescript/            # original PineScript source files
├── strategies/            # Python strategy implementations
│   ├── sma_crossover.py
│   ├── two_pole_oscillator.py
│   ├── volume_filter.py
│   └── combined.py
├── backtests/             # backtest runner scripts
│   └── run_all.py
├── results/
│   └── stats.csv
└── utils/
    ├── data_fetcher.py    # OHLCV data download
    └── stats_logger.py    # CSV logging
```

## Setup

```bash
pip install -r requirements.txt
```

## Usage

### Fetch data and run all backtests:
```bash
cd backtests
python run_all.py
```

### Fetch data only:
```bash
python -m utils.data_fetcher
```

## Results

Results are saved to `results/stats.csv` with columns:
- strategy_name, pair, roi, drawdown, sharpe, sortino, win_rate, num_trades, expected_value

Each strategy file also gets stats comments at the top after running.

## Adding New Strategies

1. Create a new file in `strategies/`
2. Implement a class extending `backtesting.Strategy`
3. Add it to `STRATEGIES` dict in `backtests/run_all.py`
4. Run the backtests

## Disclaimer

This is for educational and research purposes only. Not financial advice. Past performance does not guarantee future results. Always do your own research and manage risk appropriately.
