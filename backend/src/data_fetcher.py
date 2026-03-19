"""Fetch ETF price data via yfinance."""

import time

import pandas as pd
import yfinance as yf


def fetch_prices(
    tickers: list[str],
    start: str,
    end: str,
    fields: list[str] | None = None,
    max_retries: int = 3,
) -> dict[str, pd.DataFrame]:
    """Fetch OHLC price data for given tickers.

    Returns dict with keys like 'Close', 'Open', each a DataFrame
    indexed by date with columns = tickers.
    """
    if fields is None:
        fields = ["Close", "Open"]

    data = None
    for attempt in range(max_retries):
        try:
            data = yf.download(
                tickers,
                start=start,
                end=end,
                auto_adjust=True,
                progress=False,
                threads=False,  # Avoid SQLite locking issues
            )
            if data is not None and not data.empty:
                break
        except Exception as e:
            print(f"  Fetch attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

    if data is None or data.empty:
        raise RuntimeError(f"Failed to fetch data for {tickers} after {max_retries} attempts")

    result = {}
    for field in fields:
        if len(tickers) == 1:
            df = data[field].to_frame(name=tickers[0])
        else:
            df = data[field]
        # Drop rows where all values are NaN
        df = df.dropna(how="all")
        # Forward-fill gaps up to 3 days
        df = df.ffill(limit=3)
        result[field] = df

    return result
