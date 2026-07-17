import numpy as np
import pytest

from src.backtest.metrics import (
    compute_lift,
    compute_ndcg,
    compute_precision_at_k,
    compute_recall_at_k,
)


def test_perfect_ranking_metrics():
    truth = [1, 1, 0, 0]
    scores = [0.9, 0.8, 0.2, 0.1]
    assert compute_precision_at_k(truth, scores, 2) == 1.0
    assert compute_recall_at_k(truth, scores, 2) == 1.0
    assert compute_lift(truth, scores, 2) == 2.0
    assert compute_ndcg(truth, scores, 4) == 1.0


@pytest.mark.parametrize(
    "truth,scores,k",
    [([], [], 1), ([1], [0.1, 0.2], 1), ([2], [0.1], 1), ([1], [np.nan], 1)],
)
def test_invalid_metric_inputs_raise(truth, scores, k):
    with pytest.raises(ValueError):
        compute_precision_at_k(truth, scores, k)
