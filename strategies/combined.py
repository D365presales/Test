# ============================================================
# Strategy: Combined_Strategy
# Pair: BTC/USD
# ROI: -3.17%
# Max Drawdown: 3.91%
# Sharpe Ratio: -1.4081
# Sortino Ratio: -0.2132
# Win Rate: 0.0%
# Number of Trades: 5
# Expected Value/Trade: $-6.34
# ============================================================
# ============================================================
# Strategy: Combined_Strategy
# Pair: ETH/USD
# ROI: 7.17%
# Max Drawdown: 4.79%
# Sharpe Ratio: 0.7777
# Sortino Ratio: 0.2971
# Win Rate: 40.0%
# Number of Trades: 5
# Expected Value/Trade: $14.33
# ============================================================
# ============================================================
# Strategy: Combined_Strategy
# Pair: SOL/USD
# ROI: 23.96%
# Max Drawdown: 10.25%
# Sharpe Ratio: 1.5382
# Sortino Ratio: 0.5525
# Win Rate: 42.86%
# Number of Trades: 7
# Expected Value/Trade: $34.23
# ============================================================
"""
Combined Strategy — All three indicators as confluence.
LONG ONLY — Spot trading, no leverage.

Entry requires ALL of:
1. SMA20 > SMA200 (golden cross regime)
2. Two-Pole Oscillator buy signal (crosses above signal in oversold zone)
3. Volume > 1.5x 20-period average (volume confirmation)

Exit on ANY of:
- SMA20 < SMA200 (death cross)
- Two-Pole Oscillator sell signal
- Price drops below SMA20
"""

import numpy as np
import pandas as pd
from backtesting import Strategy
from strategies.two_pole_oscillator import compute_oscillator


class CombinedStrategy(Strategy):
    """
    Combined confluence strategy using SMA crossover, Two-Pole Oscillator,
    and volume confirmation. All three must align for entry.
    LONG ONLY.
    """
    sma_fast = 20
    sma_slow = 200
    filter_length = 20
    osc_sma_length = 25
    volume_period = 20
    volume_multiplier = 1.5

    def init(self):
        close = pd.Series(self.data.Close)
        volume = pd.Series(self.data.Volume)

        self.sma20 = self.I(lambda x: x.rolling(self.sma_fast).mean(), close, name="SMA20")
        self.sma200 = self.I(lambda x: x.rolling(self.sma_slow).mean(), close, name="SMA200")

        osc, signal = compute_oscillator(close, self.osc_sma_length, self.filter_length)
        self.osc = self.I(lambda: osc, name="TwoPole_Osc", overlay=False)
        self.osc_signal = self.I(lambda: signal, name="TwoPole_Signal", overlay=False)

        self.avg_vol = self.I(lambda x: x.rolling(self.volume_period).mean(), volume, name="AvgVol")

    def next(self):
        if len(self.osc) < 2:
            return

        sma20 = self.sma20[-1]
        sma200 = self.sma200[-1]

        if np.isnan(sma20) or np.isnan(sma200) or np.isnan(self.avg_vol[-1]):
            return

        osc_now = self.osc[-1]
        osc_prev = self.osc[-2]
        sig_now = self.osc_signal[-1]
        sig_prev = self.osc_signal[-2]

        if np.isnan(osc_now) or np.isnan(sig_now) or np.isnan(osc_prev) or np.isnan(sig_prev):
            return

        price = self.data.Close[-1]
        volume = self.data.Volume[-1]
        avg_vol = self.avg_vol[-1]

        # Conditions
        sma_bullish = sma20 > sma200
        osc_buy_cross = osc_prev <= sig_prev and osc_now > sig_now and osc_now < 0
        osc_sell_cross = osc_prev >= sig_prev and osc_now < sig_now and osc_now > 0
        high_volume = volume > (self.volume_multiplier * avg_vol)

        if not self.position:
            # Entry: ALL three must align
            if sma_bullish and osc_buy_cross and high_volume:
                self.buy(size=0.99)
        else:
            # Exit on ANY bearish signal
            if not sma_bullish or osc_sell_cross or price < sma20:
                self.position.close()
