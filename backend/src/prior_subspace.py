"""Build prior subspace V0 and prior correlation matrix C0."""

import numpy as np


def build_prior_subspace(
    n_leader: int,
    n_follower: int,
    leader_cyclical: list[bool],
    follower_cyclical: list[bool],
) -> np.ndarray:
    """Build V0 matrix (N x K0) with K0=3 orthogonal prior vectors.

    Vectors:
        v1 (global): equal weight on all sectors
        v2 (country spread): +1 for leader, -1 for follower
        v3 (cyclical/defensive): +1 for cyclical, -1 for defensive
    """
    N = n_leader + n_follower

    # v1: global factor
    v1 = np.ones(N)
    v1 = v1 / np.linalg.norm(v1)

    # v2: country spread (leader positive, follower negative)
    v2 = np.concatenate([np.ones(n_leader), -np.ones(n_follower)])
    # Orthogonalize against v1 (Gram-Schmidt)
    v2 = v2 - np.dot(v2, v1) * v1
    v2 = v2 / np.linalg.norm(v2)

    # v3: cyclical/defensive
    cyclical_flags = leader_cyclical + follower_cyclical
    v3 = np.array([1.0 if c else -1.0 for c in cyclical_flags])
    # Orthogonalize against v1 and v2
    v3 = v3 - np.dot(v3, v1) * v1
    v3 = v3 - np.dot(v3, v2) * v2
    norm_v3 = np.linalg.norm(v3)
    if norm_v3 < 1e-10:
        raise ValueError("v3 is degenerate after orthogonalization. Check cyclical labels.")
    v3 = v3 / norm_v3

    V0 = np.column_stack([v1, v2, v3])
    return V0


def build_prior_correlation_matrix(
    V0: np.ndarray,
    C_full: np.ndarray,
) -> np.ndarray:
    """Build prior correlation matrix C0 from V0 and full-sample correlation matrix.

    Equations (10)-(12) from paper:
        D0 = diag(V0^T C_full V0)
        C0_raw = V0 D0 V0^T
        Delta = diag(C0_raw)
        C0 = Delta^{-1/2} C0_raw Delta^{-1/2}
    """
    # D0: eigenvalues along prior directions
    D0 = np.diag(np.diag(V0.T @ C_full @ V0))

    # Raw prior correlation structure
    C0_raw = V0 @ D0 @ V0.T

    # Normalize to correlation matrix
    Delta = np.diag(C0_raw)
    Delta_inv_sqrt = np.diag(1.0 / np.sqrt(np.maximum(Delta, 1e-10)))
    C0 = Delta_inv_sqrt @ C0_raw @ Delta_inv_sqrt

    return C0
