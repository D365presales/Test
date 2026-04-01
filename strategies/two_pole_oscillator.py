# ============================================================
# Strategy: Two_Pole_Oscillator
# Pair: BTC/USD
# ROI: -14.76%
# Max Drawdown: 37.46%
# Sharpe Ratio: -0.4365
# Sortino Ratio: -0.4079
# Win Rate: 50.0%
# Number of Trades: 36
# Expected Value/Trade: $-4.1
# ============================================================
# ============================================================
# Strategy: Two_Pole_Oscillator
# Pair: ETH/USD
# ROI: 27.66%
# Max Drawdown: 54.34%
# Sharpe Ratio: 0.7541
# Sortino Ratio: 0.7345
# Win Rate: 50.0%
# Number of Trades: 36
# Expected Value/Trade: $7.68
# ============================================================
# ============================================================
# Strategy: Two_Pole_Oscillator
# Pair: SOL/USD
# ROI: -61.08%
# Max Drawdown: 70.33%
# Sharpe Ratio: -1.5484
# Sortino Ratio: -1.455
# Win Rate: 43.24%
# Number of Trades: 37
# Expected Value/Trade: $-16.51
# ============================================================
"""
Two-Pole Oscillator Strategy (BigBeluga style)
LONG ONLY — Spot trading, no leverage.

Based on BigBeluga's TradingView indicator:
https://www.tradingview.com/script/2Ssn4yDZ-Two-Pole-Oscillator-BigBeluga/

Logic:
1. Calculate price deviation from SMA(25) mean
2. Normalize deviation: (deviation - SMA(deviation, 25)) / StdDev(deviation, 25)
3. Apply two-pole EMA filter (cascaded EMA smoothing)
4. Signal line = filtered oscillator shifted by 4 bars
5. Buy when oscillator crosses above signal line AND oscillator < 0 (oversold)
6. Sell when oscillator crosses below signal line AND oscillator > 0 (overbought)
"""

import numpy as np
import pandas as pd
from backtesting import Strategy


def two_pole_filter(source: pd.Series, length: int) -> pd.Series:
    """
    Two-pole smooth filter — cascaded EMA.
    Equivalent to BigBeluga's PineScript f_two_pole_filter function.
    """
    alpha = 2.0 / (length + 1)
    smooth1 = source.ewm(alpha=alpha, adjust=False).mean()
    smooth2 = smooth1.ewm(alpha=alpha, adjust=False).mean()
    return smooth2


def compute_oscillator(close: pd.Series, sma_length: int = 25, filter_length: int = 20) -> tuple:
    """
    Compute the BigBeluga Two-Pole Oscillator.
    Returns (oscillator, signal_line).
    """
    sma1 = close.rolling(sma_length).mean()
    deviation = close - sma1
    deviation_sma = deviation.rolling(sma_length).mean()
    deviation_std = deviation.rolling(sma_length).std()

    # Normalized deviation
    sma_n1 = (deviation - deviation_sma) / deviation_std

    # Apply two-pole filter
    osc = two_pole_filter(sma_n1, filter_length)

    # Signal line is the oscillator shifted by 4 bars
    signal = osc.shift(4)

    return osc, signal


class TwoPoleOscillator(Strategy):
    """
    Two-Pole Oscillator strategy based on BigBeluga's TradingView indicator.
    Buy when oscillator crosses above signal line in oversold territory (< 0).
    Sell when oscillator crosses below signal line in overbought territory (> 0).
    LONG ONLY.
    """
    filter_length = 20
    sma_length = 25
    lookback = 4

    def init(self):
        close = pd.Series(self.data.Close, index=self.data.index if hasattr(self.data, 'index') else range(len(self.data.Close)))
        osc, signal = compute_oscillator(close, self.sma_length, self.filter_length)
        self.osc = self.I(lambda: osc, name="TwoPole_Osc", overlay=False)
        self.signal = self.I(lambda: signal, name="TwoPole_Signal", overlay=False)

    def next(self):
        if len(self.osc) < 2:
            return

        osc_now = self.osc[-1]
        osc_prev = self.osc[-2]
        sig_now = self.signal[-1]
        sig_prev = self.signal[-2]

        if np.isnan(osc_now) or np.isnan(sig_now) or np.isnan(osc_prev) or np.isnan(sig_prev):
            return

        # Buy: oscillator crosses above signal AND oscillator is in oversold zone (< 0)
        buy_cross = osc_prev <= sig_prev and osc_now > sig_now
        if buy_cross and osc_now < 0:
            if not self.position:
                self.buy(size=0.99)

        # Sell: oscillator crosses below signal AND oscillator is in overbought zone (> 0)
        sell_cross = osc_prev >= sig_prev and osc_now < sig_now
        if sell_cross and osc_now > 0:
            if self.position:
                self.position.close()
