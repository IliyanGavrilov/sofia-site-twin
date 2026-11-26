"""Huff gravity model: how the demand of each cell splits between competing facilities.

P(i -> j) = A_j * d_ij^-beta / sum_k A_k * d_ik^-beta
"""

import numpy as np


def huff_probabilities(
    dist: np.ndarray, attractiveness=None, beta: float = 2.0, min_dist: float = 50.0
) -> np.ndarray:
    """Patronage probabilities for a (cells, facilities) distance matrix; each row sums to 1.

    ``min_dist`` caps the utility of a facility sitting on a cell centre, so one point
    cannot take a cell's whole demand at distance ~0.
    """
    if dist.shape[1] == 0:
        return np.zeros_like(dist)
    a = np.ones(dist.shape[1]) if attractiveness is None else np.asarray(attractiveness, float)
    utility = a[None, :] * np.maximum(dist, min_dist) ** -beta
    return utility / utility.sum(axis=1, keepdims=True)


def market_share(residents: np.ndarray, probs: np.ndarray) -> np.ndarray:
    """Share of all residents captured by each facility; sums to 1."""
    captured = (residents[:, None] * probs).sum(axis=0)
    total = residents.sum()
    return captured / total if total > 0 else captured
