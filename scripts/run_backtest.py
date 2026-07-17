#!/usr/bin/env python3
"""Run the reproducible synthetic backtest and publish judge-facing artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.backtest import BacktestConfig, TabularHitPredictor, TimeMachineBacktest  # noqa: E402
from src.pipeline.data_generator import generate_miniso_sample_data  # noqa: E402

DISCLAIMER = (
    "Synthetic demonstration only. The scores validate code paths and leakage "
    "controls; they are not MINISO production KPIs or evidence of business uplift."
)


def plot_metrics(results: dict, output_path: Path) -> None:
    """Render a compact comparison chart using renderer-safe Latin labels."""
    colors = {"random": "#9CA3AF", "popularity": "#F59E0B", "model": "#DC2626"}
    labels = {"random": "Random", "popularity": "Historical rate", "model": "Tabular model"}
    fig, axes = plt.subplots(2, 2, figsize=(13.5, 8.2))
    fig.patch.set_facecolor("#FAFAFA")
    panels = [
        ("precision@20", "Precision@20"),
        ("recall@20", "Recall@20"),
        ("lift@20", "Lift@20"),
        ("ndcg@20", "NDCG@20"),
    ]
    for axis, (metric, title) in zip(axes.flat, panels, strict=True):
        for name, result in results.items():
            axis.plot(
                range(1, len(result.timestamps) + 1),
                result.metrics[metric],
                marker="o",
                markersize=3.8,
                linewidth=1.8,
                color=colors[name],
                label=labels[name],
            )
        axis.set_title(title, loc="left", fontsize=12, fontweight="bold")
        axis.set_xlabel("Rolling window")
        axis.grid(alpha=0.22)
        axis.spines[["top", "right"]].set_visible(False)
        if metric == "lift@20":
            axis.axhline(1.0, color="#6B7280", linestyle="--", linewidth=1)
    handles, legend_labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(
        handles,
        legend_labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.94),
        ncol=3,
        frameon=False,
    )
    fig.suptitle(
        "Time-machine backtest | synthetic evidence level",
        x=0.06,
        y=0.995,
        ha="left",
        fontsize=16,
        fontweight="bold",
    )
    fig.text(0.06, 0.015, DISCLAIMER, fontsize=8.5, color="#6B7280")
    fig.tight_layout(rect=(0.04, 0.05, 0.98, 0.88))
    fig.savefig(output_path, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def run_experiment(output_dir: Path, n_products: int = 2_400) -> dict:
    data = generate_miniso_sample_data(n_products=n_products, n_days=720, seed=42)
    config = BacktestConfig(
        train_window=180,
        gap_days=14,
        pred_window=90,
        stride=30,
        min_samples=80,
        random_seed=2026,
    )
    backtest = TimeMachineBacktest(config)
    predictors = {
        "random": backtest.random_baseline,
        "popularity": backtest.popularity_baseline,
        "model": TabularHitPredictor(random_state=config.random_seed),
    }
    results = {name: backtest.run(data, predictor) for name, predictor in predictors.items()}

    output_dir.mkdir(parents=True, exist_ok=True)
    plot_metrics(results, output_dir / "backtest_metrics.png")
    summary_rows = []
    for name, result in results.items():
        summary_rows.append({"method": name, **result.avg_metrics})
    pd.DataFrame(summary_rows).to_csv(output_dir / "backtest_summary.csv", index=False)

    protocol = asdict(config)
    protocol["protected_columns"] = sorted({"is_hit", *config.leakage_cols})

    payload = {
        "evidence_level": "synthetic_demo",
        "disclaimer": DISCLAIMER,
        "generated_by": "scripts/run_backtest.py",
        "dataset": {
            "generator": "synthetic-demo-v2",
            "n_products": len(data),
            "date_min": str(data["date"].min().date()),
            "date_max": str(data["date"].max().date()),
            "hit_rate": float(data["is_hit"].mean()),
        },
        "protocol": protocol,
        "results": {
            name: {
                "completed_windows": len(result.timestamps),
                "skipped_windows": result.skipped_windows,
                "average_metrics": result.avg_metrics,
                "window_audit": result.pred_details,
            }
            for name, result in results.items()
        },
    }
    (output_dir / "metrics.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "artifacts" / "demo",
        help="Directory for JSON, CSV and PNG artifacts.",
    )
    parser.add_argument("--n-products", type=int, default=2_400)
    args = parser.parse_args()
    payload = run_experiment(args.output_dir, n_products=args.n_products)

    print(DISCLAIMER)
    print(f"Artifacts: {args.output_dir.resolve()}")
    for name, result in payload["results"].items():
        metrics = result["average_metrics"]
        print(
            f"{name:>10}: P@20={metrics['precision@20']:.3f} "
            f"Lift@20={metrics['lift@20']:.3f} NDCG@20={metrics['ndcg@20']:.3f}"
        )


if __name__ == "__main__":
    main()
