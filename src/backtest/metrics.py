"""Ranking metrics used by the time-machine backtest.

All public functions validate their inputs.  Silent truncation and empty-array
division are particularly dangerous in an offline evaluation because they can
turn a broken experiment into a plausible-looking score.
"""

from collections.abc import Sequence

import numpy as np


def _validate_inputs(
    y_true: Sequence[int],
    y_score: Sequence[float],
    k: int,
) -> tuple[np.ndarray, np.ndarray, int]:
    """Return validated one-dimensional arrays and an effective ``k``."""
    truth = np.asarray(y_true)
    scores = np.asarray(y_score, dtype=float)

    if truth.ndim != 1 or scores.ndim != 1:
        raise ValueError("y_true and y_score must be one-dimensional")
    if len(truth) == 0:
        raise ValueError("y_true and y_score must not be empty")
    if len(truth) != len(scores):
        raise ValueError("y_true and y_score must have the same length")
    if k <= 0:
        raise ValueError("k must be a positive integer")
    if not np.isfinite(scores).all():
        raise ValueError("y_score contains NaN or infinite values")
    if not np.isin(truth, [0, 1]).all():
        raise ValueError("y_true must contain binary labels 0 or 1")

    return truth.astype(int), scores, min(k, len(truth))


def compute_precision_at_k(
    y_true: Sequence[int],
    y_score: Sequence[float],
    k: int = 20,
) -> float:
    """
    计算 Precision@K

    Args:
        y_true: 真实标签 (1=爆品, 0=非爆品)
        y_score: 模型预测得分
        k: Top-K 数量

    Returns:
        Precision@K = TP@K / K
    """
    truth, scores, k = _validate_inputs(y_true, y_score, k)

    # ``mergesort`` is stable, so ties remain reproducible.
    top_k_idx = np.argsort(-scores, kind="mergesort")[:k]
    top_k_true = truth[top_k_idx]

    return float(top_k_true.sum() / k)


def compute_lift(
    y_true: Sequence[int],
    y_score: Sequence[float],
    k: int = 20,
) -> float:
    """
    计算 Lift@K (vs 随机基线)

    Lift = Precision@K / (整体爆品率)

    Returns:
        Lift@K 值
    """
    truth, scores, k = _validate_inputs(y_true, y_score, k)
    base_rate = np.mean(truth)
    if base_rate == 0:
        return 0.0

    prec_k = compute_precision_at_k(truth, scores, k)
    return prec_k / base_rate


def compute_recall_at_k(
    y_true: Sequence[int],
    y_score: Sequence[float],
    k: int = 20,
) -> float:
    """Compute the share of all positives recovered in the top ``k``."""
    truth, scores, k = _validate_inputs(y_true, y_score, k)
    positives = int(truth.sum())
    if positives == 0:
        return 0.0
    order = np.argsort(-scores, kind="mergesort")[:k]
    return float(truth[order].sum() / positives)


def compute_ndcg(
    y_true: Sequence[int],
    y_score: Sequence[float],
    k: int = 20,
) -> float:
    """
    计算 NDCG@K (归一化折损累计增益)

    NDCG = DCG / IDCG
    DCG = sum((2^rel_i - 1) / log2(i+1))
    """
    y_true, y_score, k = _validate_inputs(y_true, y_score, k)

    # 按得分排序
    order = np.argsort(-y_score, kind="mergesort")
    rel = y_true[order][:k]

    # DCG
    dcg = 0.0
    for i, r in enumerate(rel):
        dcg += (2**r - 1) / np.log2(i + 2)  # i+2 because log2(1)=0

    # IDCG (理想排序)
    ideal_order = np.argsort(-y_true, kind="mergesort")
    ideal_rel = y_true[ideal_order][:k]
    idcg = 0.0
    for i, r in enumerate(ideal_rel):
        idcg += (2**r - 1) / np.log2(i + 2)

    if idcg == 0:
        return 0.0

    return dcg / idcg


def compute_all_metrics(
    y_true: Sequence[int],
    y_score: Sequence[float],
    ks: list[int] = None,
) -> dict:
    """
    一次性计算所有指标

    Returns:
        {"precision@5": ..., "lift@20": ..., "ndcg@20": ..., ...}
    """
    if ks is None:
        ks = [5, 10, 20, 50]

    metrics = {}
    for k in ks:
        metrics[f"precision@{k}"] = compute_precision_at_k(y_true, y_score, k)
        metrics[f"recall@{k}"] = compute_recall_at_k(y_true, y_score, k)
        metrics[f"lift@{k}"] = compute_lift(y_true, y_score, k)
        metrics[f"ndcg@{k}"] = compute_ndcg(y_true, y_score, k)

    return metrics
