"""
时光机回测引擎 (Time-Machine Backtest Engine)
============================================
⭐ 核心创新：滚动时间窗回测框架

Protocol 定义:
  1. 数据切片: 按时间将数据分为训练窗 + 空白间隔 + 预测窗
  2. 基线: 随机排序 / 历史爆品率 / 简单流行度
  3. 指标: Precision@K / Lift / NDCG / 帕累托前沿
  4. 校准: 锚定回归 + 方差修正 + 保形预测
"""

import numpy as np
import pandas as pd
from typing import Optional, Callable
from dataclasses import dataclass, field
from .metrics import compute_all_metrics


@dataclass
class BacktestConfig:
    """回测配置"""
    train_window: int = 180          # 训练窗口天数
    gap_days: int = 14               # 空白间隔（模拟"未来不可知"）
    pred_window: int = 90            # 预测窗口天数
    stride: int = 30                 # 滚动步长
    top_k: list[int] = field(default_factory=lambda: [5, 10, 20, 50])
    min_samples: int = 50            # 最小样本数


@dataclass
class BacktestResult:
    """回测结果"""
    metrics: dict[str, list[float]]  # 每个时间窗的指标
    timestamps: list[str]            # 时间窗标签
    avg_metrics: dict[str, float]    # 平均指标
    pred_details: list[dict]         # 每条预测详情


class TimeMachineBacktest:
    """
    时光机回测引擎

    使用方法:
        backtest = TimeMachineBacktest(config)
        results = backtest.run(data, predictor_fn)
    """

    def __init__(self, config: BacktestConfig = None):
        self.config = config or BacktestConfig()

    def run(
        self,
        df: pd.DataFrame,
        predictor_fn: Callable,
        date_col: str = "date",
        label_col: str = "is_hit",
        id_col: str = "product_id",
    ) -> BacktestResult:
        """
        执行滚动时间窗回测

        Args:
            df: 历史数据，需包含日期、标签、特征
            predictor_fn: 预测函数 f(train_df, pred_df) -> scores
            date_col: 日期列名
            label_col: 标签列名 (1=爆品, 0=非爆品)
            id_col: 产品ID列名

        Returns:
            BacktestResult 包含所有指标
        """
        cfg = self.config
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        dates = sorted(df[date_col].unique())

        all_metrics = {f"precision@{k}": [] for k in cfg.top_k}
        all_metrics.update({f"lift@{k}": [] for k in cfg.top_k})
        all_metrics["ndcg@20"] = []
        all_metrics["ndcg@50"] = []
        timestamps = []
        pred_details = []

        # 滚动窗口
        for i in range(len(dates)):
            train_end = dates[i] + pd.Timedelta(days=cfg.train_window)
            if train_end >= dates[-1]:
                break

            # 跳过（空白间隔）
            pred_start = train_end + pd.Timedelta(days=cfg.gap_days)
            pred_end = pred_start + pd.Timedelta(days=cfg.pred_window)

            # 取数据
            train_mask = (df[date_col] <= train_end)
            pred_mask = (df[date_col] >= pred_start) & (df[date_col] <= pred_end)

            train_df = df[train_mask].copy()
            pred_df = df[pred_mask].copy()

            if len(pred_df) < cfg.min_samples:
                continue

            try:
                # 预测
                scores = predictor_fn(train_df, pred_df)

                if len(scores) != len(pred_df):
                    raise ValueError("预测分数长度不匹配")

                # 计算指标
                y_true = pred_df[label_col].values
                y_score = np.array(scores)

                metrics = compute_all_metrics(y_true, y_score, cfg.top_k)

                for key, val in metrics.items():
                    all_metrics[key].append(val)

                timestamps.append(f"{pred_start.date()}~{pred_end.date()}")

                # 保存详情
                pred_details.append({
                    "window": timestamps[-1],
                    "n_train": len(train_df),
                    "n_pred": len(pred_df),
                    "n_pos": int(y_true.sum()),
                    "metrics": metrics,
                })

            except Exception as e:
                print(f"窗口 {i} 回测失败: {e}")
                continue

        # 计算平均
        avg = {}
        for key, vals in all_metrics.items():
            avg[key] = float(np.mean(vals)) if vals else 0.0

        return BacktestResult(
            metrics=all_metrics,
            timestamps=timestamps,
            avg_metrics=avg,
            pred_details=pred_details,
        )

    @staticmethod
    def random_baseline(train_df: pd.DataFrame, pred_df: pd.DataFrame) -> np.ndarray:
        """随机基线预测器"""
        return np.random.random(len(pred_df))

    @staticmethod
    def popularity_baseline(train_df: pd.DataFrame, pred_df: pd.DataFrame) -> np.ndarray:
        """基于历史流行度的基线"""
        if "social_score" in train_df.columns:
            avg_score = train_df["social_score"].mean()
        else:
            avg_score = train_df["is_hit"].mean()
        return np.full(len(pred_df), avg_score)

    def summary(self, result: BacktestResult) -> str:
        """生成回测摘要文本"""
        lines = ["=" * 60, "📊 时光机回测摘要", "=" * 60]
        lines.append(f"回测配置: 训练{self.config.train_window}d + 间隔{self.config.gap_days}d + 预测{self.config.pred_window}d")
        lines.append(f"滚动次数: {len(result.timestamps)}")
        lines.append("")

        for key, val in sorted(result.avg_metrics.items()):
            lines.append(f"  {key}: {val:.4f}")

        lines.append("")
        lines.append(f"最佳 Precision@20: {max(result.metrics.get('precision@20', [0])):.4f}")
        lines.append(f"最佳 Lift@20: {max(result.metrics.get('lift@20', [1])):.4f}")

        return "\n".join(lines)
