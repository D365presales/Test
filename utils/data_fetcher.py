"""
OHLCV data fetcher using ccxt.
Downloads 4H candles for configured pairs and caches to CSV.
Uses Binance as primary (better pagination) with USDT pairs, falls back to Kraken.
"""

import os
import time
import ccxt
import pandas as pd
from datetime import datetime, timedelta, timezone

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def fetch_ohlcv(pair: str, timeframe: str = None, days: int = None) -> pd.DataFrame:
    """
    Fetch OHLCV data for a pair.
    Tries Binance first (with USDT conversion), then Kraken.
    Returns DataFrame with columns: Open, High, Low, Close, Volume
    """
    timeframe = timeframe or config.TIMEFRAME
    days = days or config.LOOKBACK_DAYS

    since = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000)

    # Try exchanges in order
    exchanges_to_try = [
        ("binance", pair.replace("/USD", "/USDT")),
        ("kraken", pair),
    ]

    for exchange_id, fetch_pair in exchanges_to_try:
        try:
            exchange_class = getattr(ccxt, exchange_id)
            exchange = exchange_class({"enableRateLimit": True})

            all_ohlcv = []
            current_since = since
            limit = 1000

            print(f"  Fetching {pair} ({fetch_pair}) {timeframe} from {exchange_id}...")

            while True:
                ohlcv = exchange.fetch_ohlcv(fetch_pair, timeframe, since=current_since, limit=limit)
                if not ohlcv:
                    break

                all_ohlcv.extend(ohlcv)
                current_since = ohlcv[-1][0] + 1

                if len(ohlcv) < limit:
                    break

                time.sleep(exchange.rateLimit / 1000)

            if all_ohlcv:
                df = pd.DataFrame(all_ohlcv, columns=["timestamp", "Open", "High", "Low", "Close", "Volume"])
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                df.set_index("timestamp", inplace=True)
                df = df[~df.index.duplicated(keep="first")]
                df.sort_index(inplace=True)

                print(f"  Fetched {len(df)} candles for {pair} ({df.index[0]} to {df.index[-1]})")
                return df

        except Exception as e:
            print(f"  {exchange_id} failed for {pair}: {e}")
            continue

    raise ValueError(f"Could not fetch data for {pair} from any exchange")


def save_data(df: pd.DataFrame, pair: str) -> str:
    """Save OHLCV data to CSV cache."""
    os.makedirs(config.DATA_DIR, exist_ok=True)
    filename = pair.replace("/", "_") + f"_{config.TIMEFRAME}.csv"
    filepath = os.path.join(config.DATA_DIR, filename)
    df.to_csv(filepath)
    print(f"  Saved to {filepath}")
    return filepath


def load_data(pair: str) -> pd.DataFrame:
    """Load cached OHLCV data from CSV."""
    filename = pair.replace("/", "_") + f"_{config.TIMEFRAME}.csv"
    filepath = os.path.join(config.DATA_DIR, filename)

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No cached data for {pair}. Run fetch first.")

    df = pd.read_csv(filepath, index_col=0, parse_dates=True)
    return df


def fetch_all(force: bool = False):
    """Fetch and cache data for all configured pairs."""
    for pair in config.PAIRS:
        filename = pair.replace("/", "_") + f"_{config.TIMEFRAME}.csv"
        filepath = os.path.join(config.DATA_DIR, filename)
        if not force and os.path.exists(filepath):
            print(f"  Cached data exists for {pair}, skipping (use force=True to refetch)")
            continue
        df = fetch_ohlcv(pair)
        save_data(df, pair)
    print("All data fetched and cached.")


if __name__ == "__main__":
    fetch_all(force=True)
