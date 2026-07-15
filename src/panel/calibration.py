"""
虚拟消费者面板校准 (Virtual Consumer Panel Calibration)
====================================================
创新2: 锚定回归 + 方差修正 + 保形预测

流程:
  1. 锚定回归 (Anchor Regression): 在小样本真实数据上校准 LLM 打分
  2. 方差修正 (Variance Correction): Bootstrap 估计置信区间
  3. 保形预测 (Conformal Prediction): 无分布假设的预测集构建
"""

import numpy as np
from typing import Optional
from sklearn.linear_model import LinearRegression


class VirtualPanelCalibrator:
    """
    虚拟消费者面板校准器

    将 LLM 输出的原始评分校准为更准确的爆品概率估计，
    并提供置信区间。
    """

    def __init__(self, alpha: float = 0.1, n_bootstrap: int = 200):
        """
        Args:
            alpha: 保形预测显著性水平 (默认0.1 → 90%置信区间)
            n_bootstrap: Bootstrap 重采样次数
        """
        self.alpha = alpha
        self.n_bootstrap = n_bootstrap
        self.anchor_model: Optional[LinearRegression] = None
        self._calib_scores: list[float] = []
        self._calib_residuals: list[float] = []

    def fit_anchor(
        self,
        llm_scores: np.ndarray,
        true_scores: np.ndarray,
    ) -> "VirtualPanelCalibrator":
        """
        锚定回归: 用少量真实数据校准 LLM 评分

        Args:
            llm_scores: LLM 模型输出的原始评分 (N,)
            true_scores: 真实消费者评分/爆品标签 (N,)
        """
        X = llm_scores.reshape(-1, 1)
        y = true_scores

        self.anchor_model = LinearRegression()
        self.anchor_model.fit(X, y)

        # 保存校准残差 (用于保形预测)
        y_pred = self.anchor_model.predict(X)
        self._calib_scores = llm_scores.tolist()
        self._calib_residuals = (y - y_pred).tolist()

        r2 = self.anchor_model.score(X, y)
        print(f"[校准] 锚定回归 R² = {r2:.4f}")

        return self

    def predict(self, llm_scores: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        校准预测 + 置信区间

        Args:
            llm_scores: LLM 输出评分 (N,)

        Returns:
            (calibrated_scores, lower_bounds, upper_bounds)
        """
        if self.anchor_model is None:
            raise ValueError("请先调用 fit_anchor 进行校准")

        X = llm_scores.reshape(-1, 1)
        calib = self.anchor_model.predict(X)

        # 方差修正 (Bootstrap)
        lower, upper = self._conformal_interval(calib)

        # 裁剪到 [0, 1] 范围
        calib = np.clip(calib, 0, 1)
        lower = np.clip(lower, 0, 1)
        upper = np.clip(upper, 0, 1)

        return calib, lower, upper

    def _conformal_interval(self, preds: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """
        保形预测区间 (无分布假设)

        基于校准残差的绝对值的分位数构建预测区间。
        """
        n = len(self._calib_residuals)
        if n == 0:
            return preds, preds

        # 校准集残差绝对值
        abs_residuals = np.abs(self._calib_residuals)
        q = np.quantile(abs_residuals, 1 - self.alpha)

        # 区间宽度 = q * (预测值缩放因子)
        width = q * np.ones_like(preds)

        return preds - width, preds + width

    def bootstrap_interval(
        self,
        llm_scores: np.ndarray,
        n_iterations: int = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Bootstrap 方差修正

        Returns:
            (lower_2.5%, upper_97.5%)
        """
        if n_iterations is None:
            n_iterations = self.n_bootstrap

        n = len(self._calib_scores)
        if n == 0:
            return np.zeros(len(llm_scores)), np.ones(len(llm_scores))

        boot_preds = []
        for _ in range(n_iterations):
            # 从校准集有放回采样
            idx = np.random.choice(n, n, replace=True)
            X_boot = np.array(self._calib_scores)[idx].reshape(-1, 1)
            y_boot = np.array(self._calib_residuals)[idx]

            model = LinearRegression()
            model.fit(X_boot, y_boot)

            X_new = llm_scores.reshape(-1, 1)
            boot_preds.append(model.predict(X_new))

        boot_preds = np.array(boot_preds)
        lower = np.percentile(boot_preds, 2.5, axis=0)
        upper = np.percentile(boot_preds, 97.5, axis=0)

        return lower, upper

    def evaluate_calibration(
        self,
        llm_scores: np.ndarray,
        true_scores: np.ndarray,
        n_bins: int = 10,
    ) -> dict:
        """
        评估校准效果: 平均校准误差 (ACE)

        ACE = mean(|预测概率 - 实际频率|)
        """
        calib, _, _ = self.predict(llm_scores)

        bins = np.linspace(0, 1, n_bins + 1)
        ace = 0.0
        bin_data = []

        for i in range(n_bins):
            mask = (calib >= bins[i]) & (calib < bins[i + 1])
            if mask.sum() == 0:
                continue

            pred_prob = calib[mask].mean()
            actual_rate = true_scores[mask].mean()
            bin_ace = abs(pred_prob - actual_rate)
            ace += bin_ace
            bin_data.append({
                "bin": f"{bins[i]:.1f}-{bins[i+1]:.1f}",
                "count": int(mask.sum()),
                "pred_prob": float(pred_prob),
                "actual_rate": float(actual_rate),
                "error": float(bin_ace),
            })

        ace /= n_bins

        return {
            "ace": ace,
            "bin_data": bin_data,
            "n_samples": len(llm_scores),
            "n_bins": n_bins,
        }
