"""
OHLCV data fetcher using ccxt (crypto) and yfinance (stocks).
Downloads candles for configured pairs and caches to CSV.
Uses Binance as primary (better pagination) with USDT pairs, falls back to Kraken.
"""

import os
import re
import time
import ccxt
import pandas as pd
from datetime import datetime, timedelta, timezone

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Timeframe mapping for yfinance (ccxt format -> yfinance interval)
YFINANCE_INTERVALS = {
    "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "1h", "4h": "1h",  # yfinance doesn't support 4h natively, we resample
    "1d": "1d", "1w": "1wk", "1M": "1mo",
}

# Known stock exchanges (used to detect stock symbols)
STOCK_EXCHANGES = {"NASDAQ", "NYSE", "TSX", "TSXV", "AMEX", "ARCA"}


def is_stock_symbol(pair: str) -> bool:
    """
    Detect if a pair is a stock symbol.
    Stock format: 'AAPL', 'SHOP.TO', 'NASDAQ:AAPL'
    Crypto format: 'BTC/USD', 'ETH/USDT'
    """
    # Exchange-prefixed: NASDAQ:AAPL
    if ":" in pair:
        exchange = pair.split(":")[0].upper()
        return exchange in STOCK_EXCHANGES
    # Crypto pairs have a slash
    if "/" in pair:
        return False
    # Plain ticker (AAPL, SHOP.TO) — assume stock
    return True


def _normalize_stock_ticker(pair: str) -> str:
    """Convert exchange:TICKER to yfinance format."""
    if ":" in pair:
        exchange, ticker = pair.split(":", 1)
        exchange = exchange.upper()
        if exchange in ("TSX", "TSXV"):
            return f"{ticker}.TO"
        return ticker
    return pair


def _resample_to_4h(df: pd.DataFrame) -> pd.DataFrame:
    """Resample 1H data to 4H OHLCV bars."""
    resampled = df.resample("4h").agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Volume": "sum",
    }).dropna()
    return resampled


def fetch_stock(pair: str, timeframe: str = None, days: int = None) -> pd.DataFrame:
    """
    Fetch stock OHLCV data using yfinance.
    Supports NASDAQ, NYSE, TSX symbols.
    """
    try:
        import yfinance as yf
    except ImportError:
        raise ImportError("yfinance is required for stock data. Install with: pip install yfinance")

    timeframe = timeframe or config.TIMEFRAME
    days = days or config.LOOKBACK_DAYS

    ticker = _normalize_stock_ticker(pair)
    yf_interval = YFINANCE_INTERVALS.get(timeframe)

    if yf_interval is None:
        raise ValueError(f"Unsupported timeframe for stocks: {timeframe}")

    need_resample = (timeframe == "4h")
    fetch_interval = "1h" if need_resample else yf_interval

    # yfinance max period for intraday varies:
    # 1m: 7d, 5m/15m/30m: 60d, 1h: 730d, 1d+: unlimited
    start = datetime.now(timezone.utc) - timedelta(days=days)

    print(f"  Fetching {pair} ({ticker}) {timeframe} from yfinance...")

    stock = yf.Ticker(ticker)
    df = stock.history(start=start, interval=fetch_interval)

    if df.empty:
        raise ValueError(f"No data returned from yfinance for {ticker}")

    # Normalize columns to match our format
    df = df.rename(columns={"open": "Open", "high": "High", "low": "Low",
                            "close": "Close", "volume": "Volume"})
    # Keep only OHLCV
    df = df[["Open", "High", "Low", "Close", "Volume"]]

    if need_resample:
        df = _resample_to_4h(df)

    print(f"  Fetched {len(df)} candles for {pair} ({df.index[0]} to {df.index[-1]})")
    return df


def fetch_ohlcv(pair: str, timeframe: str = None, days: int = None) -> pd.DataFrame:
    """
    Fetch OHLCV data for a pair.
    Auto-detects stock vs crypto and routes to the right fetcher.
    For crypto: tries Binance first (with USDT conversion), then Kraken.
    For stocks: uses yfinance.
    Returns DataFrame with columns: Open, High, Low, Close, Volume
    """
    if is_stock_symbol(pair):
        return fetch_stock(pair, timeframe, days)

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


def save_data(df: pd.DataFrame, pair: str, data_dir: str = None) -> str:
    """Save OHLCV data to CSV cache."""
    data_dir = data_dir or config.DATA_DIR
    os.makedirs(data_dir, exist_ok=True)

    # Clean pair name for filename (handle both crypto BTC/USD and stock NASDAQ:AAPL)
    clean_pair = pair.replace("/", "_").replace(":", "_")
    filename = clean_pair + f"_{config.TIMEFRAME}.csv"
    filepath = os.path.join(data_dir, filename)
    df.to_csv(filepath)
    print(f"  Saved to {filepath}")
    return filepath


def load_data(pair: str, data_dir: str = None) -> pd.DataFrame:
    """Load cached OHLCV data from CSV."""
    data_dir = data_dir or config.DATA_DIR
    clean_pair = pair.replace("/", "_").replace(":", "_")
    filename = clean_pair + f"_{config.TIMEFRAME}.csv"
    filepath = os.path.join(data_dir, filename)

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No cached data for {pair}. Run fetch first.")

    df = pd.read_csv(filepath, index_col=0, parse_dates=True)
    return df


def fetch_all(force: bool = False, data_dir: str = None):
    """Fetch and cache data for all configured pairs."""
    data_dir = data_dir or config.DATA_DIR
    for pair in config.PAIRS:
        clean_pair = pair.replace("/", "_").replace(":", "_")
        filename = clean_pair + f"_{config.TIMEFRAME}.csv"
        filepath = os.path.join(data_dir, filename)
        if not force and os.path.exists(filepath):
            print(f"  Cached data exists for {pair}, skipping (use force=True to refetch)")
            continue
        df = fetch_ohlcv(pair)
        save_data(df, pair, data_dir)
    print("All data fetched and cached.")


if __name__ == "__main__":
    fetch_all(force=True)
