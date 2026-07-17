import numpy as np
import pandas as pd

from src.backtest import BacktestConfig, TimeMachineBacktest


def make_frame(n_days=400):
    dates = pd.date_range("2024-01-01", periods=n_days, freq="D")
    feature = np.linspace(0, 1, n_days)
    return pd.DataFrame(
        {
            "product_id": [f"P{i:04d}" for i in range(n_days)],
            "date": dates,
            "feature": feature,
            "is_hit": (np.arange(n_days) % 4 == 0).astype(int),
            "sales_90d": np.arange(n_days) * 10,
            "realized_margin": np.arange(n_days) * 3,
        }
    )


def test_backtest_applies_stride_and_hides_outcomes():
    seen_columns = []

    def predictor(train_df, pred_df):
        assert "is_hit" in train_df
        assert "is_hit" not in pred_df
        assert "sales_90d" not in pred_df
        assert "realized_margin" not in pred_df
        seen_columns.append(set(pred_df.columns))
        return pred_df["feature"].to_numpy()

    config = BacktestConfig(
        train_window=60,
        gap_days=7,
        pred_window=30,
        stride=30,
        top_k=(5, 10),
        min_samples=20,
    )
    result = TimeMachineBacktest(config).run(make_frame(), predictor)
    assert len(result.timestamps) == 11
    starts = [pd.Timestamp(detail["train_start"]) for detail in result.pred_details]
    assert all(
        (later - earlier).days == 30 for earlier, later in zip(starts, starts[1:], strict=False)
    )
    assert seen_columns
    assert result.pred_details[0]["embargo_days"] == 7


def test_duplicate_candidate_ids_are_rejected():
    frame = make_frame(120)
    frame.loc[1, "product_id"] = frame.loc[0, "product_id"]
    engine = TimeMachineBacktest(
        BacktestConfig(train_window=30, gap_days=1, pred_window=20, min_samples=10)
    )
    try:
        engine.run(frame, lambda train, pred: np.zeros(len(pred)))
    except ValueError as exc:
        assert "unique" in str(exc)
    else:
        raise AssertionError("duplicate candidate IDs must be rejected")
