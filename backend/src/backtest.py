"""Backtest the lead-lag strategy on historical data."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .data_fetcher import fetch_prices
from .models import AlgorithmParams, MarketPairConfig, load_config
from .prior_subspace import build_prior_correlation_matrix, build_prior_subspace
from .regularized_pca import compute_correlation_matrix, run_regularized_pca
from .returns import compute_cc_returns, compute_oc_returns
from .signal_generator import compute_factor_scores, compute_signal, assign_positions


def run_backtest(
    pair: MarketPairConfig,
    params: AlgorithmParams,
    start_date: str = "2015-01-01",
    end_date: str | None = None,
) -> pd.DataFrame:
    """Run full backtest for a market pair.

    Returns DataFrame with columns:
        date, strategy_return, cumulative_return, shock_magnitude,
        top_long, top_short
    """
    if end_date is None:
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    all_tickers = pair.leader.tickers + pair.follower.tickers
    n_leader = len(pair.leader.tickers)
    n_follower = len(pair.follower.tickers)
    L = params.rolling_window_L
    K = params.top_K
    q = params.quantile_q

    # Fetch data with buffer before start_date
    fetch_start = pd.Timestamp(start_date) - pd.tseries.offsets.BDay(L + 30)
    print(f"  Fetching data from {fetch_start.strftime('%Y-%m-%d')} to {end_date}...")

    prices = fetch_prices(
        all_tickers,
        start=fetch_start.strftime("%Y-%m-%d"),
        end=end_date,
    )

    close_prices = prices["Close"]
    open_prices = prices["Open"]

    # Separate leader/follower
    leader_close = close_prices[pair.leader.tickers].dropna()
    follower_close = close_prices[pair.follower.tickers].dropna()
    follower_open = open_prices[pair.follower.tickers].dropna()

    # Compute returns
    leader_cc = compute_cc_returns(leader_close)
    follower_cc = compute_cc_returns(follower_close)
    follower_oc = compute_oc_returns(follower_open, follower_close)

    # Align all on common dates
    common_dates = leader_cc.index.intersection(follower_cc.index).intersection(follower_oc.index)
    leader_cc = leader_cc.loc[common_dates]
    follower_cc = follower_cc.loc[common_dates]
    follower_oc = follower_oc.loc[common_dates]

    # Combined returns for correlation matrix
    combined_cc = pd.concat([leader_cc, follower_cc], axis=1)

    # Build prior subspace
    V0 = build_prior_subspace(
        n_leader=n_leader,
        n_follower=n_follower,
        leader_cyclical=pair.leader.cyclical_flags,
        follower_cyclical=pair.follower.cyclical_flags,
    )

    # Pre-compute rolling means and stds
    means = combined_cc.rolling(window=L).mean()
    stds = combined_cc.rolling(window=L).std(ddof=0)
    stds = stds.replace(0, np.nan)

    # Find valid start index (need L days of history)
    valid_start = combined_cc.index[L + 1]
    if pd.Timestamp(start_date) > valid_start:
        valid_start = pd.Timestamp(start_date)

    # Filter to backtest period
    test_dates = combined_cc.index[combined_cc.index >= valid_start]
    print(f"  Backtesting {len(test_dates)} trading days...")

    results = []

    for i, date in enumerate(test_dates[:-1]):  # -1 because we need next day return
        next_date = test_dates[i + 1]

        # Standardize using rolling stats (shifted by 1)
        mu = means.loc[:date].iloc[-2]  # mean from previous window
        sigma = stds.loc[:date].iloc[-2]

        if sigma.isna().any():
            continue

        # Get window of standardized returns
        window_end_idx = combined_cc.index.get_loc(date)
        window_start_idx = max(0, window_end_idx - L)
        window_data = combined_cc.iloc[window_start_idx:window_end_idx]

        if len(window_data) < L:
            continue

        # Standardize the window
        Z_window = ((window_data - mu) / sigma).values

        if np.isnan(Z_window).any():
            continue

        # Compute C_full from window for prior (simplified: use window itself)
        C_full = compute_correlation_matrix(Z_window)
        C0 = build_prior_correlation_matrix(V0, C_full)

        # Run regularized PCA
        try:
            V_U, V_J, _ = run_regularized_pca(
                Z_window=Z_window,
                C0=C0,
                lambda_reg=params.lambda_reg,
                K=K,
                n_leader=n_leader,
                n_follower=n_follower,
            )
        except Exception:
            continue

        # Today's US standardized returns
        z_U_today = ((leader_cc.loc[date] - mu[:n_leader]) / sigma[:n_leader]).values
        if np.isnan(z_U_today).any():
            continue

        # Generate signal
        f_t = compute_factor_scores(V_U, z_U_today)
        signal_scores = compute_signal(V_J, f_t)
        positions = assign_positions(signal_scores, q)

        # Next day's actual open-to-close returns for follower
        actual_returns = follower_oc.loc[next_date].values

        # Compute strategy return (equal weight long/short)
        n_long = sum(1 for p in positions if p == "long")
        n_short = sum(1 for p in positions if p == "short")

        if n_long == 0 or n_short == 0:
            continue

        strategy_return = 0.0
        for j, pos in enumerate(positions):
            if pos == "long":
                strategy_return += actual_returns[j] / n_long
            elif pos == "short":
                strategy_return -= actual_returns[j] / n_short

        # Track results
        shock_mag = float(np.linalg.norm(f_t))
        ranked = np.argsort(signal_scores)[::-1]
        top_long = pair.follower.sectors[ranked[0]].name
        top_short = pair.follower.sectors[ranked[-1]].name

        results.append({
            "date": next_date.strftime("%Y-%m-%d"),
            "strategy_return": float(strategy_return),
            "shock_magnitude": shock_mag,
            "top_long": top_long,
            "top_short": top_short,
        })

        if (i + 1) % 500 == 0:
            print(f"    {i + 1}/{len(test_dates)} days processed...")

    df = pd.DataFrame(results)
    if len(df) == 0:
        return df

    # Compute cumulative return
    df["cumulative_return"] = (1 + df["strategy_return"]).cumprod()

    # Compute running max and drawdown
    df["running_max"] = df["cumulative_return"].cummax()
    df["drawdown"] = df["cumulative_return"] / df["running_max"] - 1

    return df


def compute_stats(df: pd.DataFrame) -> dict:
    """Compute performance statistics from backtest results."""
    if len(df) == 0:
        return {}

    returns = df["strategy_return"]
    n_days = len(returns)
    n_years = n_days / 252

    # Annualized return
    total_return = df["cumulative_return"].iloc[-1]
    ar = (total_return ** (1 / n_years) - 1) * 100 if n_years > 0 else 0

    # Annualized risk (std)
    risk = returns.std() * np.sqrt(252) * 100

    # Risk/Return ratio
    rr = ar / risk if risk > 0 else 0

    # Max drawdown
    mdd = df["drawdown"].min() * 100

    # Sharpe ratio (assuming 0 risk-free rate)
    sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0

    # Win rate
    win_rate = (returns > 0).mean() * 100

    return {
        "period": f"{df['date'].iloc[0]} to {df['date'].iloc[-1]}",
        "trading_days": n_days,
        "annualized_return_pct": round(ar, 2),
        "annualized_risk_pct": round(risk, 2),
        "risk_return_ratio": round(rr, 2),
        "sharpe_ratio": round(sharpe, 2),
        "max_drawdown_pct": round(mdd, 2),
        "total_return_x": round(total_return, 2),
        "win_rate_pct": round(win_rate, 1),
    }


def main():
    parser = argparse.ArgumentParser(description="Backtest lead-lag strategy")
    parser.add_argument("--config", default=str(Path(__file__).parent.parent / "config" / "market_pairs.yaml"))
    parser.add_argument("--output", default=str(Path(__file__).parent.parent.parent / "data"))
    parser.add_argument("--pair", default="us_japan")
    parser.add_argument("--start", default="2015-01-01")
    parser.add_argument("--end", default=None)
    args = parser.parse_args()

    params, pairs = load_config(args.config)
    pair = next((p for p in pairs if p.id == args.pair), None)
    if not pair:
        print(f"Pair '{args.pair}' not found")
        sys.exit(1)

    print(f"Backtesting {pair.name}...")
    df = run_backtest(pair, params, start_date=args.start, end_date=args.end)

    if len(df) == 0:
        print("No results generated")
        sys.exit(1)

    stats = compute_stats(df)
    print(f"\n=== {pair.name} Backtest Results ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    # Save results
    output_dir = Path(args.output) / args.pair
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save backtest summary
    backtest_data = {
        "market_pair_id": args.pair,
        "market_pair_name": pair.name,
        "stats": stats,
        "equity_curve": [
            {"date": row["date"], "cumulative_return": round(row["cumulative_return"], 4)}
            for _, row in df.iterrows()
        ],
    }

    with open(output_dir / "backtest.json", "w") as f:
        json.dump(backtest_data, f, indent=2)

    print(f"\nSaved to {output_dir / 'backtest.json'}")


if __name__ == "__main__":
    main()
