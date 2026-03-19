"""Generate lead-lag trading signals from PCA results."""

import numpy as np

from .models import SectorConfig, SectorSignal


def compute_factor_scores(
    V_U: np.ndarray,
    z_U_t: np.ndarray,
) -> np.ndarray:
    """Project US standardized returns onto common factors.

    f_t = (V_U^(K))^T @ z_U,t   (K-vector)
    """
    return V_U.T @ z_U_t


def compute_signal(
    V_J: np.ndarray,
    factor_scores: np.ndarray,
) -> np.ndarray:
    """Map factor scores to target market signal.

    z_hat_{J,t+1} = V_J^(K) @ f_t   (N_J-vector)
    """
    return V_J @ factor_scores


def assign_positions(
    signal_scores: np.ndarray,
    quantile_q: float,
) -> list[str]:
    """Assign long/short/neutral based on signal percentiles.

    Top q -> long, bottom q -> short, rest neutral.
    """
    n = len(signal_scores)
    sorted_indices = np.argsort(signal_scores)

    n_short = max(1, int(np.floor(n * quantile_q)))
    n_long = max(1, int(np.floor(n * quantile_q)))

    positions = ["neutral"] * n
    # Bottom q% -> short
    for i in sorted_indices[:n_short]:
        positions[i] = "short"
    # Top q% -> long
    for i in sorted_indices[-n_long:]:
        positions[i] = "long"

    return positions


def generate_sector_signals(
    V_U: np.ndarray,
    V_J: np.ndarray,
    z_U_t: np.ndarray,
    follower_sectors: list[SectorConfig],
    quantile_q: float,
) -> tuple[list[SectorSignal], dict[str, float], float]:
    """Full signal generation pipeline.

    Returns:
        sector_signals: ranked list of SectorSignal
        factor_scores_dict: named factor scores
        shock_magnitude: norm of factor scores
    """
    f_t = compute_factor_scores(V_U, z_U_t)
    signal_scores = compute_signal(V_J, f_t)
    positions = assign_positions(signal_scores, quantile_q)

    # Rank by signal score (descending)
    ranked_indices = np.argsort(signal_scores)[::-1]

    sector_signals = []
    for rank, idx in enumerate(ranked_indices, 1):
        sector = follower_sectors[idx]
        sector_signals.append(
            SectorSignal(
                ticker=sector.ticker,
                name=sector.name,
                signal_score=float(signal_scores[idx]),
                position=positions[idx],
                rank=rank,
            )
        )

    # Named factor scores
    factor_names = ["global", "country_spread", "cyclical_defensive"]
    factor_scores_dict = {
        name: float(f_t[i]) for i, name in enumerate(factor_names[: len(f_t)])
    }

    shock_magnitude = float(np.linalg.norm(f_t))

    return sector_signals, factor_scores_dict, shock_magnitude
