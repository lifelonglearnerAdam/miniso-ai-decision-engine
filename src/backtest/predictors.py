"""Leakage-aware baseline predictor used by the reproducible demo."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


class TabularHitPredictor:
    """Fit a small, interpretable classifier inside each backtest window.

    The predictor only uses the explicitly allow-listed features.  Outcome
    columns are never selected, even if they are present in the historical
    training frame.
    """

    categorical_features = ["category", "price_tier", "style", "material"]
    numeric_features = [
        "price",
        "estimated_unit_cost",
        "social_score",
        "trend_score",
    ]

    def __init__(self, random_state: int = 2026):
        self.random_state = random_state

    def __call__(self, train_df: pd.DataFrame, pred_df: pd.DataFrame) -> np.ndarray:
        missing = [
            col
            for col in self.categorical_features + self.numeric_features
            if col not in train_df.columns or col not in pred_df.columns
        ]
        if missing:
            raise ValueError(f"predictor is missing required features: {sorted(set(missing))}")
        if "is_hit" not in train_df.columns:
            raise ValueError("training data must contain the historical is_hit label")

        y = train_df["is_hit"].astype(int)
        if y.nunique() < 2:
            return np.full(len(pred_df), float(y.mean()))

        categorical = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="most_frequent")),
                (
                    "onehot",
                    OneHotEncoder(handle_unknown="ignore", min_frequency=2),
                ),
            ]
        )
        numeric = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scale", StandardScaler()),
            ]
        )
        features = self.categorical_features + self.numeric_features
        preprocessor = ColumnTransformer(
            [
                ("categorical", categorical, self.categorical_features),
                ("numeric", numeric, self.numeric_features),
            ]
        )
        model = Pipeline(
            [
                ("preprocess", preprocessor),
                (
                    "model",
                    LogisticRegression(
                        max_iter=500,
                        class_weight="balanced",
                        random_state=self.random_state,
                    ),
                ),
            ]
        )
        model.fit(train_df[features], y)
        return model.predict_proba(pred_df[features])[:, 1]
