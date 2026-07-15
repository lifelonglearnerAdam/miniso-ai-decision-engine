"""
社媒趋势与销售数据的相关性 & Granger 因果分析
===========================================
支撑创新5: 证明社媒信号对销量的预测能力
"""

import numpy as np
import pandas as pd
from typing import Optional
from statsmodels.tsa.stattools import grangercausalitytests, adfuller
from scipy.stats import pearsonr, spearmanr


class SocialSalesCorrelation:
    """
    社媒-销售相关性分析
    """

    def __init__(self, min_periods: int = 30):
        self.min_periods = min_periods

    def pearson_correlation(
        self,
        social_metrics: pd.Series,
        sales_metrics: pd.Series,
    ) -> dict:
        """Pearson 线性相关"""
        valid = ~(social_metrics.isna() | sales_metrics.isna())
        if valid.sum() < self.min_periods:
            return {"pearson_r": 0, "pearson_p": 1.0, "n": 0}

        r, p = pearsonr(social_metrics[valid], sales_metrics[valid])
        return {"pearson_r": r, "pearson_p": p, "n": int(valid.sum())}

    def spearman_correlation(
        self,
        social_metrics: pd.Series,
        sales_metrics: pd.Series,
    ) -> dict:
        """Spearman 秩相关 (对非线性关系鲁棒)"""
        valid = ~(social_metrics.isna() | sales_metrics.isna())
        if valid.sum() < self.min_periods:
            return {"spearman_r": 0, "spearman_p": 1.0, "n": 0}

        r, p = spearmanr(social_metrics[valid], sales_metrics[valid])
        return {"spearman_r": r, "spearman_p": p, "n": int(valid.sum())}

    def lag_correlation(
        self,
        social: pd.Series,
        sales: pd.Series,
        max_lag: int = 14,
    ) -> dict[int, float]:
        """滞後相关性分析 (社媒趋势领先销售几天)"""
        results = {}
        for lag in range(1, max_lag + 1):
            social_shifted = social.shift(-lag)
            valid = ~(social_shifted.isna() | sales.isna())
            if valid.sum() >= self.min_periods:
                r, _ = spearmanr(social_shifted[valid], sales[valid])
                results[lag] = r
        return results

    def plot_heatmap_data(
        self,
        df: pd.DataFrame,
        social_cols: list[str],
        sales_col: str,
    ) -> pd.DataFrame:
        """生成相关性热力图数据"""
        results = []
        for col in social_cols:
            corr = self.pearson_correlation(df[col], df[sales_col])
            results.append({
                "social_metric": col,
                "pearson_r": corr["pearson_r"],
                "pearson_p": corr["pearson_p"],
            })
        return pd.DataFrame(results)


class GrangerCausalAnalyzer:
    """
    Granger 因果检验分析器

    检验：社媒趋势是否能"Granger 引起"销售变化
    H0: 社媒信号不能 Granger 引起销售变化
    """

    def __init__(self, max_lag: int = 7, significance: float = 0.05):
        """
        Args:
            max_lag: 最大滞后阶数
            significance: 显著性阈值
        """
        self.max_lag = max_lag
        self.significance = significance
        self.results: dict = {}

    def check_stationarity(self, series: pd.Series, name: str = "") -> dict:
        """ADF 单位根检验 (检查平稳性)"""
        result = adfuller(series.dropna(), autolag="AIC")
        return {
            "series": name,
            "adf_stat": result[0],
            "p_value": result[1],
            "is_stationary": result[1] < self.significance,
            "critical_values": result[4],
        }

    def make_stationary(self, series: pd.Series) -> pd.Series:
        """一阶差分使序列平稳"""
        return series.diff().dropna()

    def test_causality(
        self,
        social_series: pd.Series,
        sales_series: pd.Series,
        test: str = "ssr_chi2test",
    ) -> dict:
        """
        执行 Granger 因果检验

        Args:
            social_series: 社媒趋势时间序列
            sales_series: 销售数据时间序列
            test: 检验统计量方法

        Returns:
            dict: {
                "min_p_value": 最小 p 值,
                "best_lag": 最优滞后阶数,
                "is_causal": 是否 Granger 因果,
                "detail": 各滞后阶数结果
            }
        """
        # 构建联合 DataFrame
        data = pd.DataFrame({
            "social": social_series,
            "sales": sales_series,
        }).dropna()

        if len(data) < self.max_lag + 10:
            return {
                "min_p_value": 1.0,
                "best_lag": 0,
                "is_causal": False,
                "detail": {},
                "error": "样本量不足",
            }

        try:
            # Granger 检验: sales <- social (社媒→销售)
            gc_result = grangercausalitytests(
                data[["sales", "social"]],
                maxlag=self.max_lag,
                verbose=False,
            )

            # 分析结果
            min_p = 1.0
            best_lag = 0
            detail = {}

            for lag, result in gc_result.items():
                p_value = result[0][test][1]
                detail[int(lag)] = {
                    "ssr_chi2_stat": float(result[0][test][0]),
                    "p_value": float(p_value),
                    "is_significant": p_value < self.significance,
                }
                if p_value < min_p:
                    min_p = p_value
                    best_lag = lag

            # 反向检验: social <- sales (销售→社媒, 反向因果)
            reverse_result = grangercausalitytests(
                data[["social", "sales"]],
                maxlag=self.max_lag,
                verbose=False,
            )
            reverse_min_p = min(
                (reverse_result[lag][0][test][1] for lag in reverse_result)
            )

            result = {
                "min_p_value": float(min_p),
                "best_lag": best_lag,
                "is_causal": min_p < self.significance,
                "reverse_min_p": float(reverse_min_p),
                "is_bidirectional": min_p < self.significance and reverse_min_p < self.significance,
                "detail": detail,
                "n_samples": len(data),
            }

            self.results = result
            return result

        except Exception as e:
            return {
                "min_p_value": 1.0,
                "best_lag": 0,
                "is_causal": False,
                "detail": {},
                "error": str(e),
            }

    def multi_product_analysis(
        self,
        df: pd.DataFrame,
        product_col: str = "product_id",
        social_col: str = "social_score",
        sales_col: str = "sales",
        date_col: str = "date",
    ) -> pd.DataFrame:
        """
        多产品批量 Granger 因果分析

        Returns:
            DataFrame 包含每个产品的检验结果
        """
        results = []
        for product_id, group in df.groupby(product_col):
            group = group.sort_values(date_col)
            social = group[social_col]
            sales = group[sales_col]

            # 平稳性检验
            social_stationary = self.check_stationarity(social, f"social_{product_id}")
            sales_stationary = self.check_stationarity(sales, f"sales_{product_id}")

            # 如不平稳则差分
            if not social_stationary["is_stationary"]:
                social = self.make_stationary(social)
            if not sales_stationary["is_stationary"]:
                sales = self.make_stationary(sales)

            gc = self.test_causality(social, sales)

            results.append({
                "product_id": product_id,
                "n_observations": len(group),
                "social_stationary": social_stationary["is_stationary"],
                "sales_stationary": sales_stationary["is_stationary"],
                "is_causal": gc["is_causal"],
                "min_p_value": gc["min_p_value"],
                "best_lag": gc["best_lag"],
                "reverse_causal": gc.get("reverse_min_p", 1.0) < self.significance,
                "bidirectional": gc.get("is_bidirectional", False),
            })

        return pd.DataFrame(results)

    @staticmethod
    def format_result(result: dict) -> str:
        """格式化分析报告"""
        if "error" in result:
            return f"❌ 分析失败: {result['error']}"

        status = "✅ 有 Granger 因果关系" if result["is_causal"] else "❌ 无显著 Granger 因果关系"
        return (
            f"Granger 因果分析结果:\n"
            f"  {status}\n"
            f"  最优滞后: {result['best_lag']} 天\n"
            f"  最小 p 值: {result['min_p_value']:.4f}\n"
            f"  样本量: {result['n_samples']}\n"
            f"  反向检验 p: {result.get('reverse_min_p', 'N/A'):.4f}\n"
            f"  双向因果: {'是' if result.get('is_bidirectional') else '否'}"
        )
