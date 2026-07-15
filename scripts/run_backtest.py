#!/usr/bin/env python3
"""
运行时光机回测，生成 Precision@K/Lift/NDCG 图表
=============================================
用法: python scripts/run_backtest.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import matplotlib
matplotlib.use("Agg")  # 无 GUI 后端
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from src.backtest import TimeMachineBacktest, BacktestConfig
from src.pipeline.data_generator import generate_miniso_sample_data


def smart_predictor(train_df, pred_df):
    """智能预测器：基于产品属性打分"""
    scores = []
    for _, row in pred_df.iterrows():
        base = 0.1
        if row.get("social_score", 0) > 0.7:
            base += 0.3
        if row.get("style") in ["国潮", "IP联名"]:
            base += 0.15
        if row.get("category") in ["美妆", "家居"]:
            base += 0.1
        if row.get("day_on_market", 30) < 7:
            base -= 0.1
        scores.append(min(base + np.random.random() * 0.2, 1.0))
    return np.array(scores)


def plot_metrics(random_results, smart_results, output_dir="."):
    """绘制回测指标对比图"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("时光机回测结果 — Precision@K / Lift / NDCG", fontsize=16)

    # Precision@20
    ax = axes[0, 0]
    ts = smart_results.timestamps
    ax.plot(ts, random_results.metrics.get("precision@20", []), "o-", label="随机基线", alpha=0.6)
    ax.plot(ts, smart_results.metrics.get("precision@20", []), "s-", label="AI智能预测", linewidth=2)
    ax.set_title("Precision@20 (滚动时间窗)")
    ax.set_xlabel("时间窗")
    ax.set_ylabel("Precision@20")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # Lift@20
    ax = axes[0, 1]
    ax.plot(ts, random_results.metrics.get("lift@20", []), "o-", label="随机基线", alpha=0.6)
    ax.plot(ts, smart_results.metrics.get("lift@20", []), "s-", label="AI智能预测", linewidth=2)
    ax.axhline(y=1.0, color="gray", linestyle="--", label="无提升 (Lift=1)")
    ax.set_title("Lift@20")
    ax.set_xlabel("时间窗")
    ax.set_ylabel("Lift")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # NDCG
    ax = axes[1, 0]
    ndcg_data = {
        "Random@20": [random_results.avg_metrics.get("ndcg@20", 0)],
        "AI@20": [smart_results.avg_metrics.get("ndcg@20", 0)],
        "Random@50": [random_results.avg_metrics.get("ndcg@50", 0)],
        "AI@50": [smart_results.avg_metrics.get("ndcg@50", 0)],
    }
    x = np.arange(len(ndcg_data))
    bars = ax.bar(x, [v[0] for v in ndcg_data.values()], width=0.5)
    bars[1].set_color("#FF6B6B")
    bars[3].set_color("#FF6B6B")
    ax.set_xticks(x)
    ax.set_xticklabels(ndcg_data.keys())
    ax.set_title("NDCG@K 对比")
    ax.set_ylabel("NDCG")
    ax.axhline(y=0.5, color="gray", linestyle="--", alpha=0.5)
    ax.grid(True, alpha=0.3, axis="y")
    for bar, val in zip(bars, ndcg_data.values()):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                f"{val[0]:.3f}", ha="center", va="bottom", fontsize=10)

    # 摘要
    ax = axes[1, 1]
    ax.axis("off")
    summary_lines = [
        "📊 回测摘要",
        "",
        f"回测窗口: {len(smart_results.timestamps)}",
        f"训练/间隔/预测: 180d/14d/90d",
        "",
        "AI 预测 vs 随机基线:",
    ]
    for key in ["precision@20", "lift@20", "ndcg@20"]:
        sv = smart_results.avg_metrics.get(key, 0)
        rv = random_results.avg_metrics.get(key, 0)
        diff = (sv - rv) / rv if rv > 0 else 0
        summary_lines.append(f"  {key}: {sv:.4f} vs {rv:.4f} (↑{diff:+.1%})")

    summary_lines.extend([
        "",
        f"最佳 Precision@20: {max(smart_results.metrics.get('precision@20', [0])):.4f}",
        f"最佳 Lift@20: {max(smart_results.metrics.get('lift@20', [1])):.4f}",
    ])

    ax.text(0.05, 0.95, "\n".join(summary_lines),
            transform=ax.transAxes, fontsize=11, verticalalignment="top",
            fontfamily="monospace", bbox=dict(boxstyle="round", facecolor="lightyellow"))

    plt.tight_layout()
    path = os.path.join(output_dir, "backtest_results.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    print(f"[图表] 已保存: {path}")
    plt.close()


def main():
    print("=" * 60)
    print("🕰️ 时光机回测 — 生成回测实验报告图表")
    print("=" * 60)

    # 生成数据
    print("\n[1/4] 生成合成数据...")
    data = generate_miniso_sample_data(n_products=500, n_days=365)

    # 配置
    config = BacktestConfig(
        train_window=180,
        gap_days=14,
        pred_window=90,
        stride=30,
    )

    # 运行回测
    print("\n[2/4] 运行随机基线...")
    backtest = TimeMachineBacktest(config)
    random_results = backtest.run(data, backtest.random_baseline)

    print("\n[3/4] 运行 AI 智能预测...")
    smart_results = backtest.run(data, smart_predictor)

    # 输出摘要
    print("\n" + "-" * 40)
    print("随机基线:")
    print(backtest.summary(random_results))
    print("\nAI 智能预测:")
    print(backtest.summary(smart_results))

    # 绘图
    print("\n[4/4] 生成图表...")
    output_dir = os.path.join(os.path.dirname(__file__), "..", "docs", "03_回测实验报告")
    os.makedirs(output_dir, exist_ok=True)
    plot_metrics(random_results, smart_results, output_dir)

    print("\n✅ 回测完成！图表已保存至 docs/03_回测实验报告/")


if __name__ == "__main__":
    main()
