# ============================================================
# Strategy: Volume_Filter
# Pair: BTC/USD
# ROI: -16.98%
# Max Drawdown: 28.86%
# Sharpe Ratio: -0.7637
# Sortino Ratio: -0.612
# Win Rate: 24.56%
# Number of Trades: 57
# Expected Value/Trade: $-2.98
# ============================================================
# ============================================================
# Strategy: Volume_Filter
# Pair: ETH/USD
# ROI: 45.19%
# Max Drawdown: 32.47%
# Sharpe Ratio: 1.1499
# Sortino Ratio: 1.1156
# Win Rate: 33.9%
# Number of Trades: 59
# Expected Value/Trade: $7.66
# ============================================================
# ============================================================
# Strategy: Volume_Filter
# Pair: SOL/USD
# ROI: -14.73%
# Max Drawdown: 42.37%
# Sharpe Ratio: -0.1966
# Sortino Ratio: -0.1751
# Win Rate: 36.51%
# Number of Trades: 63
# Expected Value/Trade: $-2.34
# ============================================================
"""
Volume Profile / Volume Confirmation Strategy
LONG ONLY — Spot trading, no leverage.

Entry: Close > SMA(20) AND volume > 1.5x 20-period average volume
Exit:  Close < SMA(20) OR volume spike on a down candle

This is a trend-following strategy with volume confirmation.
A simple moving average defines the trend, and above-average volume
confirms conviction behind the move.
"""

import numpy as np
import pandas as pd
from backtesting import Strategy


class VolumeFilter(Strategy):
    """
    Volume-confirmed trend strategy.
    Entry: Price above SMA(20) + volume > 1.5x average volume.
    Exit: Price crosses below SMA(20).
    LONG ONLY.
    """
    sma_period = 20
    volume_period = 20
    volume_multiplier = 1.5

    def init(self):
        close = pd.Series(self.data.Close)
        volume = pd.Series(self.data.Volume)

        self.sma = self.I(lambda x: x.rolling(self.sma_period).mean(), close, name="SMA20")
        self.avg_vol = self.I(lambda x: x.rolling(self.volume_period).mean(), volume, name="AvgVol")

    def next(self):
        if np.isnan(self.sma[-1]) or np.isnan(self.avg_vol[-1]):
            return

        price = self.data.Close[-1]
        volume = self.data.Volume[-1]
        sma_val = self.sma[-1]
        avg_vol_val = self.avg_vol[-1]

        # Entry: price above SMA + high volume
        high_volume = volume > (self.volume_multiplier * avg_vol_val)

        if not self.position:
            if price > sma_val and high_volume:
                self.buy(size=0.99)

        # Exit: price below SMA
        else:
            if price < sma_val:
                self.position.close()
