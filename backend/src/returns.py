"""Compute and standardize returns."""

import numpy as np
import pandas as pd


def compute_cc_returns(close_prices: pd.DataFrame) -> pd.DataFrame:
    """Close-to-close returns: P_close_t / P_close_{t-1} - 1"""
    return close_prices.pct_change().iloc[1:]


def compute_oc_returns(open_prices: pd.DataFrame, close_prices: pd.DataFrame) -> pd.DataFrame:
    """Open-to-close returns: P_close_t / P_open_t - 1"""
    return (close_prices / open_prices) - 1


def standardize_returns(
    returns: pd.DataFrame,
    window_L: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Rolling standardization of returns.

    For each time t, uses window W_t = {t-L, ..., t-1} to compute
    mean and std, then standardizes returns[t].

    Returns:
        z_scores: standardized returns (only rows with full window)
        means: rolling means
        stds: rolling stds
    """
    means = returns.rolling(window=window_L).mean()
    stds = returns.rolling(window=window_L).std(ddof=0)

    # Avoid division by zero
    stds = stds.replace(0, np.nan)

    # Standardize using the rolling stats
    # Shift by 1: use stats from {t-L, ..., t-1} to standardize t
    z_scores = (returns - means.shift(1)) / stds.shift(1)

    # Drop rows without full window
    z_scores = z_scores.iloc[window_L + 1:]
    z_scores = z_scores.dropna()

    return z_scores, means, stds
