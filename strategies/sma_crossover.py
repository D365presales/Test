# ============================================================
# Strategy: SMA_20_200_Crossover
# Pair: BTC/USD
# ROI: -21.42%
# Max Drawdown: 29.48%
# Sharpe Ratio: -1.2182
# Sortino Ratio: -0.9244
# Win Rate: 12.5%
# Number of Trades: 8
# Expected Value/Trade: $-26.77
# ============================================================
# ============================================================
# Strategy: SMA_20_200_Crossover
# Pair: ETH/USD
# ROI: -6.17%
# Max Drawdown: 48.03%
# Sharpe Ratio: 0.0049
# Sortino Ratio: 0.0041
# Win Rate: 12.5%
# Number of Trades: 8
# Expected Value/Trade: $-7.71
# ============================================================
# ============================================================
# Strategy: SMA_20_200_Crossover
# Pair: SOL/USD
# ROI: -0.27%
# Max Drawdown: 32.76%
# Sharpe Ratio: 0.1761
# Sortino Ratio: 0.1633
# Win Rate: 33.33%
# Number of Trades: 6
# Expected Value/Trade: $-0.45
# ============================================================
"""
SMA 20/200 Crossover Strategy — Golden Cross / Death Cross
LONG ONLY — Spot trading, no leverage.

Entry: SMA20 crosses above SMA200
Exit:  SMA20 crosses below SMA200
"""

from backtesting import Strategy
from backtesting.lib import crossover
import pandas as pd


class SMACrossover(Strategy):
    """
    Classic SMA Golden Cross / Death Cross strategy.
    Long when SMA20 crosses above SMA200.
    Exit when SMA20 crosses below SMA200.
    """
    sma_fast = 20
    sma_slow = 200

    def init(self):
        close = pd.Series(self.data.Close)
        self.sma20 = self.I(lambda x: x.rolling(self.sma_fast).mean(), close, name="SMA20")
        self.sma200 = self.I(lambda x: x.rolling(self.sma_slow).mean(), close, name="SMA200")

    def next(self):
        # LONG ONLY
        if crossover(self.sma20, self.sma200):
            if not self.position:
                self.buy(size=0.99)  # 100% of capital (0.99 to avoid rounding issues)

        elif crossover(self.sma200, self.sma20):
            if self.position:
                self.position.close()
