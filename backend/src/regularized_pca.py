"""Core algorithm: subspace-regularized PCA."""

import numpy as np


def compute_correlation_matrix(Z: np.ndarray) -> np.ndarray:
    """Compute correlation matrix from standardized returns matrix.

    Args:
        Z: (L x N) standardized return matrix for window W_t
    Returns:
        C: (N x N) sample correlation matrix
    """
    L, N = Z.shape
    C = (Z.T @ Z) / L
    return C


def regularize_correlation(
    C_t: np.ndarray,
    C0: np.ndarray,
    lambda_reg: float,
) -> np.ndarray:
    """Regularized correlation matrix: C_t^reg = (1 - lambda) * C_t + lambda * C0

    Args:
        C_t: sample correlation matrix (N x N)
        C0: prior correlation matrix (N x N)
        lambda_reg: regularization parameter in [0, 1]
    """
    return (1 - lambda_reg) * C_t + lambda_reg * C0


def extract_top_eigenvectors(
    C_reg: np.ndarray,
    K: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Eigendecompose and extract top K eigenvectors.

    Returns:
        V_K: (N x K) top K eigenvectors
        eigenvalues: top K eigenvalues (descending)
    """
    eigenvalues, eigenvectors = np.linalg.eigh(C_reg)

    # eigh returns ascending order; reverse for descending
    idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[idx[:K]]
    V_K = eigenvectors[:, idx[:K]]

    return V_K, eigenvalues


def split_eigenvectors(
    V_K: np.ndarray,
    n_leader: int,
    n_follower: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Split eigenvectors into leader and follower blocks.

    Args:
        V_K: (N x K) eigenvectors where N = n_leader + n_follower
    Returns:
        V_U: (n_leader x K) leader block
        V_J: (n_follower x K) follower block
    """
    V_U = V_K[:n_leader, :]
    V_J = V_K[n_leader:n_leader + n_follower, :]
    return V_U, V_J


def run_regularized_pca(
    Z_window: np.ndarray,
    C0: np.ndarray,
    lambda_reg: float,
    K: int,
    n_leader: int,
    n_follower: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Full regularized PCA pipeline for one time step.

    Args:
        Z_window: (L x N) standardized returns for the estimation window
        C0: (N x N) prior correlation matrix
        lambda_reg: regularization strength
        K: number of top eigenvectors
        n_leader: number of leader (US) sectors
        n_follower: number of follower (target) sectors

    Returns:
        V_U: (n_leader x K) leader eigenvector block
        V_J: (n_follower x K) follower eigenvector block
        eigenvalues: top K eigenvalues
    """
    C_t = compute_correlation_matrix(Z_window)
    C_reg = regularize_correlation(C_t, C0, lambda_reg)
    V_K, eigenvalues = extract_top_eigenvectors(C_reg, K)
    V_U, V_J = split_eigenvectors(V_K, n_leader, n_follower)
    return V_U, V_J, eigenvalues
