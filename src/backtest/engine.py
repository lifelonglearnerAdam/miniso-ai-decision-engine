"""Leakage-aware rolling time-machine backtest.

The engine evaluates a predictor at historical decision cut-offs.  Training,
embargo and prediction windows are disjoint; the configured stride is applied
explicitly; and protected outcome columns are removed before candidates are
given to a predictor.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .metrics import compute_all_metrics


@dataclass(frozen=True)
class BacktestConfig:
    """Configuration for a rolling-origin evaluation."""

    train_window: int = 180
    gap_days: int = 14
    pred_window: int = 90
    stride: int = 30
    top_k: tuple[int, ...] = (5, 10, 20, 50)
    min_samples: int = 30
    random_seed: int = 2026
    leakage_cols: tuple[str, ...] = ("sales_90d", "realized_margin")

    def __post_init__(self) -> None:
        if self.train_window <= 0 or self.pred_window <= 0 or self.stride <= 0:
            raise ValueError("train_window, pred_window and stride must be positive")
        if self.gap_days < 0:
            raise ValueError("gap_days must not be negative")
        if self.min_samples <= 0:
            raise ValueError("min_samples must be positive")
        if not self.top_k or any(k <= 0 for k in self.top_k):
            raise ValueError("top_k must contain positive integers")


@dataclass
class BacktestResult:
    """Metrics and audit details for all completed windows."""

    metrics: dict[str, list[float]]
    timestamps: list[str]
    avg_metrics: dict[str, float]
    pred_details: list[dict]
    skipped_windows: list[dict] = field(default_factory=list)


class TimeMachineBacktest:
    """Evaluate a ranking model without crossing the historical cut-off."""

    def __init__(self, config: BacktestConfig | None = None):
        self.config = config or BacktestConfig()

    @staticmethod
    def _validate_frame(
        df: pd.DataFrame,
        date_col: str,
        label_col: str,
        id_col: str,
    ) -> pd.DataFrame:
        missing = [col for col in (date_col, label_col, id_col) if col not in df.columns]
        if missing:
            raise ValueError(f"backtest data is missing columns: {missing}")
        if df.empty:
            raise ValueError("backtest data must not be empty")

        frame = df.copy()
        frame[date_col] = pd.to_datetime(frame[date_col], errors="raise")
        if frame[id_col].isna().any() or frame[id_col].duplicated().any():
            raise ValueError("each candidate must have a unique, non-null product_id")
        if not frame[label_col].isin([0, 1]).all():
            raise ValueError("label column must contain binary values 0 or 1")
        return frame.sort_values([date_col, id_col]).reset_index(drop=True)

    def run(
        self,
        df: pd.DataFrame,
        predictor_fn: Callable[[pd.DataFrame, pd.DataFrame], Sequence[float]],
        date_col: str = "date",
        label_col: str = "is_hit",
        id_col: str = "product_id",
    ) -> BacktestResult:
        """Run rolling-origin evaluation and return an auditable result.

        ``predictor_fn`` receives historical rows including their labels, plus a
        candidate frame with the label and configured leakage columns removed.
        """

        cfg = self.config
        frame = self._validate_frame(df, date_col, label_col, id_col)
        min_date = frame[date_col].min().normalize()
        max_date = frame[date_col].max().normalize()

        metric_names = []
        for k in cfg.top_k:
            metric_names.extend([f"precision@{k}", f"recall@{k}", f"lift@{k}", f"ndcg@{k}"])
        all_metrics = {name: [] for name in metric_names}
        timestamps: list[str] = []
        pred_details: list[dict] = []
        skipped_windows: list[dict] = []

        train_start = min_date
        window_index = 0
        while True:
            train_end = train_start + pd.Timedelta(days=cfg.train_window - 1)
            pred_start = train_end + pd.Timedelta(days=cfg.gap_days + 1)
            pred_end = pred_start + pd.Timedelta(days=cfg.pred_window - 1)
            if pred_end > max_date:
                break

            train_mask = frame[date_col].between(train_start, train_end, inclusive="both")
            pred_mask = frame[date_col].between(pred_start, pred_end, inclusive="both")
            train_df = frame.loc[train_mask].copy()
            pred_df = frame.loc[pred_mask].copy()
            label = f"{pred_start.date()}~{pred_end.date()}"

            if len(train_df) < cfg.min_samples or len(pred_df) < cfg.min_samples:
                skipped_windows.append(
                    {
                        "window": label,
                        "reason": "insufficient_samples",
                        "n_train": len(train_df),
                        "n_pred": len(pred_df),
                    }
                )
            elif pred_df[label_col].nunique() < 2:
                skipped_windows.append(
                    {
                        "window": label,
                        "reason": "single_class_prediction_window",
                        "n_train": len(train_df),
                        "n_pred": len(pred_df),
                    }
                )
            else:
                protected = {label_col, *cfg.leakage_cols}
                pred_input = pred_df.drop(
                    columns=[col for col in protected if col in pred_df.columns]
                )
                scores = np.asarray(predictor_fn(train_df.copy(), pred_input), dtype=float)
                if scores.ndim != 1 or len(scores) != len(pred_df):
                    raise ValueError(
                        f"predictor returned shape {scores.shape}; expected ({len(pred_df)},)"
                    )
                if not np.isfinite(scores).all():
                    raise ValueError("predictor returned NaN or infinite scores")

                y_true = pred_df[label_col].to_numpy(dtype=int)
                metrics = compute_all_metrics(y_true, scores, list(cfg.top_k))
                for key in all_metrics:
                    all_metrics[key].append(float(metrics[key]))

                timestamps.append(label)
                pred_details.append(
                    {
                        "window_index": window_index,
                        "window": label,
                        "train_start": str(train_start.date()),
                        "train_end": str(train_end.date()),
                        "embargo_days": cfg.gap_days,
                        "pred_start": str(pred_start.date()),
                        "pred_end": str(pred_end.date()),
                        "n_train": len(train_df),
                        "n_pred": len(pred_df),
                        "n_pos": int(y_true.sum()),
                        "protected_columns": sorted(protected),
                        "metrics": metrics,
                    }
                )

            window_index += 1
            train_start += pd.Timedelta(days=cfg.stride)

        averages = {
            key: float(np.mean(values)) if values else 0.0 for key, values in all_metrics.items()
        }
        return BacktestResult(
            metrics=all_metrics,
            timestamps=timestamps,
            avg_metrics=averages,
            pred_details=pred_details,
            skipped_windows=skipped_windows,
        )

    def random_baseline(self, train_df: pd.DataFrame, pred_df: pd.DataFrame) -> np.ndarray:
        """Stable pseudo-random ranking for a reproducible comparison."""
        del train_df
        if "product_id" in pred_df:
            hashed = pd.util.hash_pandas_object(pred_df["product_id"], index=False).to_numpy()
            # Map the stable 64-bit hashes into [0, 1).
            return (hashed % 10_000_019) / 10_000_019
        rng = np.random.default_rng(self.config.random_seed)
        return rng.random(len(pred_df))

    @staticmethod
    def popularity_baseline(train_df: pd.DataFrame, pred_df: pd.DataFrame) -> np.ndarray:
        """Smoothed historical hit rate by category with a global fallback."""
        if "is_hit" not in train_df:
            raise ValueError("historical baseline requires is_hit in training data")
        global_rate = float(train_df["is_hit"].mean())
        if "category" not in train_df or "category" not in pred_df:
            return np.full(len(pred_df), global_rate)

        stats = train_df.groupby("category")["is_hit"].agg(["sum", "count"])
        smoothing = 20.0
        rates = (stats["sum"] + smoothing * global_rate) / (stats["count"] + smoothing)
        return pred_df["category"].map(rates).fillna(global_rate).to_numpy(dtype=float)

    def summary(self, result: BacktestResult) -> str:
        """Create a compact, truthful summary for logs and demos."""
        lines = [
            "=" * 60,
            "Time-machine backtest summary (synthetic demonstration)",
            "=" * 60,
            (
                f"Protocol: train={self.config.train_window}d, "
                f"embargo={self.config.gap_days}d, "
                f"predict={self.config.pred_window}d, stride={self.config.stride}d"
            ),
            f"Completed windows: {len(result.timestamps)}",
            f"Skipped windows: {len(result.skipped_windows)}",
            "",
        ]
        for key, value in sorted(result.avg_metrics.items()):
            lines.append(f"  {key}: {value:.4f}")

        precision = result.metrics.get("precision@20", [])
        lift = result.metrics.get("lift@20", [])
        lines.extend(
            [
                "",
                f"Best Precision@20: {max(precision) if precision else 0.0:.4f}",
                f"Best Lift@20: {max(lift) if lift else 0.0:.4f}",
                "Evidence level: synthetic; not a production KPI or business claim.",
            ]
        )
        return "\n".join(lines)
