"""Calibration and uncertainty for a synthetic consumer panel.

The calibrator deliberately separates anchor fitting from conformal residual
calibration.  It is a decision-support component, not a substitute for real
consumer research or a claim that LLM personas reproduce a population.
"""

from __future__ import annotations

import math

import numpy as np
from sklearn.linear_model import LinearRegression


class VirtualPanelCalibrator:
    """Map raw panel scores to an observed target scale with intervals."""

    def __init__(
        self,
        alpha: float = 0.1,
        n_bootstrap: int = 500,
        calibration_fraction: float = 0.25,
        random_state: int = 2026,
    ):
        if not 0 < alpha < 1:
            raise ValueError("alpha must be between 0 and 1")
        if n_bootstrap <= 0:
            raise ValueError("n_bootstrap must be positive")
        if not 0.1 <= calibration_fraction <= 0.5:
            raise ValueError("calibration_fraction must be between 0.1 and 0.5")

        self.alpha = alpha
        self.n_bootstrap = n_bootstrap
        self.calibration_fraction = calibration_fraction
        self.random_state = random_state
        self.anchor_model: LinearRegression | None = None
        self._anchor_scores = np.array([], dtype=float)
        self._anchor_targets = np.array([], dtype=float)
        self._calib_residuals = np.array([], dtype=float)
        self.fit_diagnostics: dict[str, float | int] = {}

    @staticmethod
    def _validate_pair(scores: np.ndarray, targets: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        scores = np.asarray(scores, dtype=float).reshape(-1)
        targets = np.asarray(targets, dtype=float).reshape(-1)
        if len(scores) != len(targets):
            raise ValueError("scores and targets must have the same length")
        if len(scores) < 12:
            raise ValueError("at least 12 observations are required for split calibration")
        if not np.isfinite(scores).all() or not np.isfinite(targets).all():
            raise ValueError("scores and targets must be finite")
        return scores, targets

    def fit_anchor(
        self,
        llm_scores: np.ndarray,
        true_scores: np.ndarray,
    ) -> VirtualPanelCalibrator:
        """Fit on one partition and reserve another for split conformal residuals."""
        scores, targets = self._validate_pair(llm_scores, true_scores)
        rng = np.random.default_rng(self.random_state)
        order = rng.permutation(len(scores))
        n_calib = max(3, int(math.ceil(len(scores) * self.calibration_fraction)))
        calib_idx = order[:n_calib]
        anchor_idx = order[n_calib:]

        self._anchor_scores = scores[anchor_idx]
        self._anchor_targets = targets[anchor_idx]
        self.anchor_model = LinearRegression()
        self.anchor_model.fit(self._anchor_scores.reshape(-1, 1), self._anchor_targets)

        calib_pred = self.anchor_model.predict(scores[calib_idx].reshape(-1, 1))
        self._calib_residuals = np.abs(targets[calib_idx] - calib_pred)
        self.fit_diagnostics = {
            "n_total": len(scores),
            "n_anchor": len(anchor_idx),
            "n_conformal": len(calib_idx),
            "anchor_r2": float(
                self.anchor_model.score(self._anchor_scores.reshape(-1, 1), self._anchor_targets)
            ),
        }
        return self

    def predict(self, llm_scores: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return calibrated scores and finite-sample split-conformal intervals."""
        if self.anchor_model is None:
            raise ValueError("fit_anchor must be called before predict")
        scores = np.asarray(llm_scores, dtype=float).reshape(-1)
        if not np.isfinite(scores).all():
            raise ValueError("llm_scores must be finite")
        calibrated = self.anchor_model.predict(scores.reshape(-1, 1))
        lower, upper = self._conformal_interval(calibrated)
        return (
            np.clip(calibrated, 0, 1),
            np.clip(lower, 0, 1),
            np.clip(upper, 0, 1),
        )

    def _conformal_interval(self, predictions: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        n = len(self._calib_residuals)
        if n == 0:
            raise ValueError("conformal residuals are unavailable")
        quantile_level = min(1.0, math.ceil((n + 1) * (1 - self.alpha)) / n)
        width = float(np.quantile(self._calib_residuals, quantile_level, method="higher"))
        return predictions - width, predictions + width

    def bootstrap_interval(
        self,
        llm_scores: np.ndarray,
        n_iterations: int | None = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Bootstrap anchor pairs and return a 95% model-uncertainty interval."""
        if self.anchor_model is None:
            raise ValueError("fit_anchor must be called before bootstrap_interval")
        iterations = n_iterations or self.n_bootstrap
        if iterations <= 0:
            raise ValueError("n_iterations must be positive")

        new_scores = np.asarray(llm_scores, dtype=float).reshape(-1)
        rng = np.random.default_rng(self.random_state)
        n = len(self._anchor_scores)
        predictions = np.empty((iterations, len(new_scores)), dtype=float)
        for iteration in range(iterations):
            sample_idx = rng.integers(0, n, size=n)
            model = LinearRegression().fit(
                self._anchor_scores[sample_idx].reshape(-1, 1),
                self._anchor_targets[sample_idx],
            )
            predictions[iteration] = model.predict(new_scores.reshape(-1, 1))
        return (
            np.clip(np.percentile(predictions, 2.5, axis=0), 0, 1),
            np.clip(np.percentile(predictions, 97.5, axis=0), 0, 1),
        )

    def evaluate_calibration(
        self,
        llm_scores: np.ndarray,
        true_scores: np.ndarray,
        n_bins: int = 10,
    ) -> dict:
        """Compute count-weighted expected absolute calibration error."""
        if n_bins <= 1:
            raise ValueError("n_bins must be greater than one")
        scores = np.asarray(llm_scores, dtype=float).reshape(-1)
        targets = np.asarray(true_scores, dtype=float).reshape(-1)
        if len(scores) != len(targets) or len(scores) == 0:
            raise ValueError("evaluation scores and targets must be non-empty and aligned")
        calibrated, _, _ = self.predict(scores)

        bins = np.linspace(0, 1, n_bins + 1)
        bin_data = []
        weighted_error = 0.0
        for index in range(n_bins):
            if index == n_bins - 1:
                mask = (calibrated >= bins[index]) & (calibrated <= bins[index + 1])
            else:
                mask = (calibrated >= bins[index]) & (calibrated < bins[index + 1])
            count = int(mask.sum())
            if count == 0:
                continue
            prediction_mean = float(calibrated[mask].mean())
            observed_mean = float(targets[mask].mean())
            error = abs(prediction_mean - observed_mean)
            weighted_error += count / len(calibrated) * error
            bin_data.append(
                {
                    "bin": f"{bins[index]:.1f}-{bins[index + 1]:.1f}",
                    "count": count,
                    "predicted_mean": prediction_mean,
                    "observed_mean": observed_mean,
                    "absolute_error": error,
                }
            )

        return {
            "ece": float(weighted_error),
            "ace": float(weighted_error),  # Backward-compatible key.
            "bin_data": bin_data,
            "n_samples": len(scores),
            "n_bins": n_bins,
        }
