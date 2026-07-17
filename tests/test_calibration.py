import numpy as np

from src.panel import VirtualPanelCalibrator


def test_split_conformal_and_bootstrap_are_finite():
    rng = np.random.default_rng(7)
    scores = rng.uniform(0, 1, 240)
    targets = np.clip(0.1 + 0.7 * scores + rng.normal(0, 0.06, 240), 0, 1)
    calibrator = VirtualPanelCalibrator(alpha=0.1, n_bootstrap=40, random_state=7)
    calibrator.fit_anchor(scores[:160], targets[:160])

    predicted, lower, upper = calibrator.predict(scores[160:])
    boot_lower, boot_upper = calibrator.bootstrap_interval(scores[160:170])
    assert np.all(lower <= predicted)
    assert np.all(predicted <= upper)
    assert np.all(boot_lower <= boot_upper)
    assert calibrator.fit_diagnostics["n_conformal"] > 0


def test_calibration_error_is_count_weighted():
    rng = np.random.default_rng(11)
    scores = rng.uniform(0, 1, 160)
    targets = np.clip(scores + rng.normal(0, 0.05, 160), 0, 1)
    calibrator = VirtualPanelCalibrator(random_state=11).fit_anchor(scores[:100], targets[:100])
    result = calibrator.evaluate_calibration(scores[100:], targets[100:], n_bins=8)
    assert 0 <= result["ece"] <= 1
    assert result["ece"] == result["ace"]
