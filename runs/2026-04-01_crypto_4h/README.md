# Run: 2026-04-01 — Crypto 4H Backtest

## Configuration
- **Pairs:** BTC/USD, ETH/USD, SOL/USD
- **Timeframe:** 4H candles
- **Period:** ~1 year (2,190 candles per pair)
- **Initial Capital:** $1,000 CAD
- **Mode:** LONG ONLY / Spot / No leverage
- **Data Source:** Kraken (via ccxt, Binance fallback)

## Strategies Tested
1. **SMA 20/200 Crossover** — Golden cross / death cross
2. **Two-Pole Oscillator** — BigBeluga-style oversold/overbought filter
3. **Volume Filter** — Trend-following with volume confirmation
4. **Combined Strategy** — All three as confluence

## Key Results

| Strategy | Pair | ROI% | Max DD% | Sharpe | Win Rate% | Trades |
|----------|------|------|---------|--------|-----------|--------|
| SMA_20_200_Crossover | BTC/USD | -21.42 | 29.48 | -1.22 | 12.50 | 8 |
| SMA_20_200_Crossover | ETH/USD | -6.17 | 48.03 | 0.00 | 12.50 | 8 |
| SMA_20_200_Crossover | SOL/USD | -0.27 | 32.76 | 0.18 | 33.33 | 6 |
| Two_Pole_Oscillator | BTC/USD | -14.76 | 37.46 | -0.44 | 50.00 | 36 |
| Two_Pole_Oscillator | ETH/USD | 27.66 | 54.34 | 0.75 | 50.00 | 36 |
| Two_Pole_Oscillator | SOL/USD | -61.08 | 70.33 | -1.55 | 43.24 | 37 |
| Volume_Filter | BTC/USD | -16.98 | 28.86 | -0.76 | 24.56 | 57 |
| Volume_Filter | ETH/USD | 45.19 | 32.47 | 1.15 | 33.90 | 59 |
| Volume_Filter | SOL/USD | -14.73 | 42.37 | -0.20 | 36.51 | 63 |
| Combined_Strategy | BTC/USD | -3.17 | 3.91 | -1.41 | 0.00 | 5 |
| Combined_Strategy | ETH/USD | 7.17 | 4.79 | 0.78 | 40.00 | 5 |
| Combined_Strategy | SOL/USD | 23.96 | 10.25 | 1.54 | 42.86 | 7 |

## Observations
- **Best performer:** Volume_Filter on ETH/USD (+45.19% ROI, Sharpe 1.15)
- **Most consistent:** Combined_Strategy — lowest drawdowns across all pairs (3.9-10.3%)
- **Worst performer:** Two_Pole_Oscillator on SOL/USD (-61.08%, 70.33% drawdown)
- Combined confluence filtering significantly reduces drawdown at the cost of fewer trades
