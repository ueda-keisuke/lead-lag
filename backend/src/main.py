"""Main entry point: orchestrates daily signal generation."""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .data_fetcher import fetch_prices
from .models import AlgorithmParams, MarketPairConfig, SignalOutput, load_config
from .output_writer import append_history, write_index, write_latest_signal
from .prior_subspace import build_prior_correlation_matrix, build_prior_subspace
from .regularized_pca import compute_correlation_matrix, run_regularized_pca
from .snapshot_generator import generate_snapshot
from .returns import compute_cc_returns, standardize_returns
from .signal_generator import generate_sector_signals


def align_dates(leader_df: pd.DataFrame, follower_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Align leader and follower DataFrames on common trading dates."""
    common_dates = leader_df.index.intersection(follower_df.index)
    return leader_df.loc[common_dates], follower_df.loc[common_dates]


def process_market_pair(
    pair: MarketPairConfig,
    params: AlgorithmParams,
    output_dir: Path,
) -> SignalOutput | None:
    """Process a single market pair and generate signal."""
    print(f"Processing {pair.name}...")

    all_tickers = pair.leader.tickers + pair.follower.tickers
    n_leader = len(pair.leader.tickers)
    n_follower = len(pair.follower.tickers)

    # Fetch enough data: rolling window + buffer for standardization
    buffer_days = params.rolling_window_L * 3 + 30
    end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    start_date = (datetime.now(timezone.utc) - timedelta(days=buffer_days)).strftime("%Y-%m-%d")

    try:
        prices = fetch_prices(all_tickers, start=start_date, end=end_date)
    except Exception as e:
        print(f"  Error fetching data: {e}")
        return None

    close_prices = prices["Close"]

    # Check we have enough data
    if len(close_prices) < params.rolling_window_L + 10:
        print(f"  Not enough data: {len(close_prices)} rows")
        return None

    # Separate leader and follower close prices
    leader_close = close_prices[pair.leader.tickers].dropna()
    follower_close = close_prices[pair.follower.tickers].dropna()

    # Compute close-to-close returns for all
    leader_returns = compute_cc_returns(leader_close)
    follower_returns = compute_cc_returns(follower_close)

    # Align dates
    leader_returns, follower_returns = align_dates(leader_returns, follower_returns)

    if len(leader_returns) < params.rolling_window_L + 5:
        print(f"  Not enough aligned data: {len(leader_returns)} rows")
        return None

    # Combined returns for correlation matrix
    combined_returns = pd.concat([leader_returns, follower_returns], axis=1)

    # Standardize
    z_scores, _, _ = standardize_returns(combined_returns, params.rolling_window_L)
    if len(z_scores) < 2:
        print("  Not enough standardized data")
        return None

    # Build prior subspace
    V0 = build_prior_subspace(
        n_leader=n_leader,
        n_follower=n_follower,
        leader_cyclical=pair.leader.cyclical_flags,
        follower_cyclical=pair.follower.cyclical_flags,
    )

    # For C_full, use all available data in the standardized window
    Z_full = z_scores.values
    C_full = compute_correlation_matrix(Z_full)

    # Build prior correlation matrix
    C0 = build_prior_correlation_matrix(V0, C_full)

    # Use the latest window for PCA
    L = params.rolling_window_L
    Z_latest_window = Z_full[-L:, :]

    # Run regularized PCA
    V_U, V_J, eigenvalues = run_regularized_pca(
        Z_window=Z_latest_window,
        C0=C0,
        lambda_reg=params.lambda_reg,
        K=params.top_K,
        n_leader=n_leader,
        n_follower=n_follower,
    )

    # Get today's US standardized returns (last row, leader columns only)
    z_U_today = Z_full[-1, :n_leader]

    # Generate signals
    sector_signals, factor_scores, shock_magnitude = generate_sector_signals(
        V_U=V_U,
        V_J=V_J,
        z_U_t=z_U_today,
        follower_sectors=pair.follower.sectors,
        quantile_q=params.quantile_q,
    )

    # Get leader returns for display
    latest_leader_returns = leader_returns.iloc[-1]
    leader_return_list = [
        {
            "ticker": ticker,
            "name": next(s.name for s in pair.leader.sectors if s.ticker == ticker),
            "return_pct": round(float(latest_leader_returns[ticker]) * 100, 2),
        }
        for ticker in pair.leader.tickers
        if ticker in latest_leader_returns.index
    ]

    signal_output = SignalOutput(
        market_pair_id=pair.id,
        signal_date=z_scores.index[-1].strftime("%Y-%m-%d"),
        generated_at=datetime.now(timezone.utc).isoformat(),
        leader_date=leader_returns.index[-1].strftime("%Y-%m-%d"),
        leader_returns=leader_return_list,
        sector_signals=sector_signals,
        factor_scores=factor_scores,
        shock_magnitude=shock_magnitude,
    )

    # Write output
    write_latest_signal(signal_output, output_dir)
    append_history(signal_output, output_dir)
    generate_snapshot(signal_output, output_dir)

    print(f"  Signal generated for {signal_output.signal_date}")
    print(f"  Shock magnitude: {shock_magnitude:.4f}")
    print(f"  Top long: {sector_signals[0].name} ({sector_signals[0].signal_score:.4f})")
    print(f"  Top short: {sector_signals[-1].name} ({sector_signals[-1].signal_score:.4f})")

    return signal_output


def main():
    parser = argparse.ArgumentParser(description="Generate lead-lag signals")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).parent.parent / "config" / "market_pairs.yaml"),
        help="Path to market pairs config",
    )
    parser.add_argument(
        "--output",
        default=str(Path(__file__).parent.parent.parent / "data"),
        help="Output directory for JSON files",
    )
    parser.add_argument(
        "--pair",
        default=None,
        help="Process only this market pair ID",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    params, pairs = load_config(config_path)

    if args.pair:
        pairs = [p for p in pairs if p.id == args.pair]
        if not pairs:
            print(f"Market pair '{args.pair}' not found in config")
            sys.exit(1)

    results = []
    for pair in pairs:
        result = process_market_pair(pair, params, output_dir)
        if result:
            results.append(result)

    # Write index
    if results:
        pair_index = [
            {
                "id": r.market_pair_id,
                "name": next(p.name for p in pairs if p.id == r.market_pair_id),
                "latest_date": r.signal_date,
            }
            for r in results
        ]
        write_index(pair_index, output_dir)
        print(f"\nDone. Generated signals for {len(results)} market pair(s).")
    else:
        print("\nNo signals generated.")
        sys.exit(1)


if __name__ == "__main__":
    main()
