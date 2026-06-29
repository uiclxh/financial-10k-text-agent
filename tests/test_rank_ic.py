from __future__ import annotations

import numpy as np
import pytest

from text_factor_lab.models import rank_ic
from text_factor_lab.models.training import _rank_values
from text_factor_lab.ranking import tie_aware_extreme_indices, tie_aware_quantiles


def test_rank_ic_is_one_for_identical_ordering() -> None:
    values = np.array([0.1, 0.2, 0.3, 0.4])

    assert rank_ic(values, values) == pytest.approx(1.0)


def test_rank_ic_is_negative_one_for_reversed_ordering() -> None:
    y_true = np.array([0.1, 0.2, 0.3, 0.4])
    y_pred = np.array([0.4, 0.3, 0.2, 0.1])

    assert rank_ic(y_true, y_pred) == pytest.approx(-1.0)


def test_rank_ic_is_zero_for_constant_predictions() -> None:
    y_true = np.array([0.1, 0.2, 0.3, 0.4])
    y_pred = np.ones(4)

    assert rank_ic(y_true, y_pred) == 0.0


def test_rank_values_assign_average_rank_to_ties() -> None:
    values = np.array([1.0, 1.0, 2.0, 3.0])

    np.testing.assert_allclose(_rank_values(values), np.array([0.5, 0.5, 2.0, 3.0]))
    assert rank_ic(np.array([1.0, 2.0, 3.0, 4.0]), values) == pytest.approx(
        0.9486832980505139
    )


def test_rank_ic_with_ties_is_invariant_to_row_order() -> None:
    y_true = np.array([0.4, 0.1, 0.3, 0.2])
    y_pred = np.array([2.0, 1.0, 2.0, 1.0])
    permutation = np.array([2, 0, 3, 1])

    original = rank_ic(y_true, y_pred)
    permuted = rank_ic(y_true[permutation], y_pred[permutation])

    assert permuted == pytest.approx(original)


@pytest.mark.parametrize(
    ("y_true", "y_pred"),
    [
        (np.array([]), np.array([])),
        (np.array([1.0]), np.array([1.0])),
    ],
)
def test_rank_ic_is_zero_when_fewer_than_two_observations(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> None:
    assert rank_ic(y_true, y_pred) == 0.0


def test_constant_scores_have_no_portfolio_extremes_and_neutral_quantile() -> None:
    scores = np.ones(4)

    low_indices, high_indices = tie_aware_extreme_indices(scores)

    assert low_indices.size == 0
    assert high_indices.size == 0
    np.testing.assert_array_equal(tie_aware_quantiles(scores), np.array([3, 3, 3, 3]))


def test_extreme_selection_includes_all_boundary_ties() -> None:
    scores = np.array([0.0, 0.0, 0.0, 1.0, 2.0, 3.0, 4.0, 4.0, 4.0, 5.0])

    low_indices, high_indices = tie_aware_extreme_indices(scores)

    np.testing.assert_array_equal(low_indices, np.array([0, 1, 2]))
    np.testing.assert_array_equal(high_indices, np.array([6, 7, 8, 9]))


def test_extreme_selection_rejects_overlapping_tied_boundaries() -> None:
    scores = np.array([0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0])

    low_indices, high_indices = tie_aware_extreme_indices(scores)

    assert low_indices.size == 0
    assert high_indices.size == 0
