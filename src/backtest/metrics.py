"""
回测评估指标
==========
Precision@K / Lift / NDCG 计算
"""

import numpy as np
from typing import Sequence


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
    if len(y_true) < k:
        k = len(y_true)

    # 按得分降序排列
    top_k_idx = np.argsort(y_score)[::-1][:k]
    top_k_true = np.array(y_true)[top_k_idx]

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
    base_rate = np.mean(y_true)
    if base_rate == 0:
        return 1.0

    prec_k = compute_precision_at_k(y_true, y_score, k)
    return prec_k / base_rate


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
    if len(y_true) < k:
        k = len(y_true)

    y_true = np.array(y_true)
    y_score = np.array(y_score)

    # 按得分排序
    order = np.argsort(y_score)[::-1]
    rel = y_true[order][:k]

    # DCG
    dcg = 0.0
    for i, r in enumerate(rel):
        dcg += (2**r - 1) / np.log2(i + 2)  # i+2 because log2(1)=0

    # IDCG (理想排序)
    ideal_order = np.argsort(y_true)[::-1]
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
        metrics[f"lift@{k}"] = compute_lift(y_true, y_score, k)

    metrics["ndcg@20"] = compute_ndcg(y_true, y_score, 20)
    metrics["ndcg@50"] = compute_ndcg(y_true, y_score, 50)

    return metrics
