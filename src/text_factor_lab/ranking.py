from __future__ import annotations

import numpy as np


def average_ranks(values: np.ndarray, *, one_based: bool = False) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    order = np.argsort(values, kind="mergesort")
    sorted_values = values[order]
    ranks = np.empty(len(values), dtype=float)

    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and sorted_values[end] == sorted_values[start]:
            end += 1
        average_rank = (start + end - 1) / 2.0
        ranks[order[start:end]] = average_rank + (1.0 if one_based else 0.0)
        start = end
    return ranks


def tie_aware_quantiles(values: np.ndarray, *, quantile_count: int = 5) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if len(values) == 0:
        return np.array([], dtype=int)
    ranks = average_ranks(values, one_based=True)
    centered_percentiles = (ranks - 0.5) / len(values)
    quantiles = np.floor(centered_percentiles * quantile_count).astype(int) + 1
    return np.clip(quantiles, 1, quantile_count)


def tie_aware_extreme_indices(
    values: np.ndarray,
    *,
    fraction: float = 0.2,
) -> tuple[np.ndarray, np.ndarray]:
    values = np.asarray(values, dtype=float)
    if len(values) < 2 or len(np.unique(values)) < 2:
        return np.array([], dtype=int), np.array([], dtype=int)

    sorted_values = np.sort(values, kind="mergesort")
    leg_size = max(1, int(len(values) * fraction))
    low_boundary = sorted_values[leg_size - 1]
    high_boundary = sorted_values[-leg_size]
    if low_boundary >= high_boundary:
        return np.array([], dtype=int), np.array([], dtype=int)

    low_indices = np.flatnonzero(values <= low_boundary)
    high_indices = np.flatnonzero(values >= high_boundary)
    return low_indices, high_indices
