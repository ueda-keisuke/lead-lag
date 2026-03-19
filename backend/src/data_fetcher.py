"""Fetch ETF price data via yfinance."""

import pandas as pd
import yfinance as yf


def fetch_prices(
    tickers: list[str],
    start: str,
    end: str,
    fields: list[str] | None = None,
) -> dict[str, pd.DataFrame]:
    """Fetch OHLC price data for given tickers.

    Returns dict with keys like 'Close', 'Open', each a DataFrame
    indexed by date with columns = tickers.
    """
    if fields is None:
        fields = ["Close", "Open"]

    data = yf.download(
        tickers,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
    )

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
