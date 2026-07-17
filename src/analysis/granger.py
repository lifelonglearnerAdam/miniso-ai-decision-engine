"""
社媒趋势与销售数据的相关性及 Granger 预测领先性分析
=================================================
支撑创新5: 检验社媒信号能否改善销量预测，而非宣称结构因果
"""

from contextlib import redirect_stdout
from io import StringIO

import pandas as pd
from scipy.stats import pearsonr, spearmanr
from statsmodels.tsa.stattools import adfuller, grangercausalitytests


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
        """滞后相关性分析（社媒信号在 ``lag`` 天前领先销售）。"""
        results = {}
        for lag in range(1, max_lag + 1):
            # Compare sales[t] with social[t-lag].  ``shift(-lag)`` would use a
            # future social observation and reverse the intended lead direction.
            social_shifted = social.shift(lag)
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
            results.append(
                {
                    "social_metric": col,
                    "pearson_r": corr["pearson_r"],
                    "pearson_p": corr["pearson_p"],
                }
            )
        return pd.DataFrame(results)


class GrangerLeadAnalyzer:
    """
    Granger 预测领先性检验分析器

    检验：社媒滞后项是否能在给定模型和样本内改善销量预测。
    H0: 社媒滞后项不能改善销量预测。

    该检验不识别结构因果；营销、节日、渠道和价格等共同因素仍可能
    同时驱动社媒与销量。
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

    def test_predictive_lead(
        self,
        social_series: pd.Series,
        sales_series: pd.Series,
        test: str = "ssr_chi2test",
    ) -> dict:
        """
        执行 Granger 预测领先性检验

        Args:
            social_series: 社媒趋势时间序列
            sales_series: 销售数据时间序列
            test: 检验统计量方法

        Returns:
            dict: {
                "min_p_value": 最小 p 值,
                "best_lag": 最优滞后阶数,
                "is_predictive_lead": 社媒滞后项是否显著改善预测,
                "detail": 各滞后阶数结果
            }
        """
        # 构建联合 DataFrame
        data = pd.DataFrame(
            {
                "social": social_series,
                "sales": sales_series,
            }
        ).dropna()

        if len(data) < self.max_lag + 10:
            return {
                "min_p_value": 1.0,
                "best_lag": 0,
                "is_predictive_lead": False,
                "is_causal": False,
                "detail": {},
                "error": "样本量不足",
                "interpretation": "predictive_lead_not_structural_causality",
            }

        try:
            # Granger 检验: sales <- social (社媒→销售)
            with redirect_stdout(StringIO()):
                gc_result = grangercausalitytests(
                    data[["sales", "social"]],
                    maxlag=self.max_lag,
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

            # 反向检验: social <- sales，用于识别双向预测关系。
            with redirect_stdout(StringIO()):
                reverse_result = grangercausalitytests(
                    data[["social", "sales"]],
                    maxlag=self.max_lag,
                )
            reverse_min_p = min(reverse_result[lag][0][test][1] for lag in reverse_result)

            is_predictive_lead = bool(min_p < self.significance)
            result = {
                "min_p_value": float(min_p),
                "best_lag": best_lag,
                "is_predictive_lead": is_predictive_lead,
                # Backward-compatible alias. New consumers should use
                # ``is_predictive_lead`` to avoid a structural-causality claim.
                "is_causal": is_predictive_lead,
                "reverse_min_p": float(reverse_min_p),
                "is_bidirectional": is_predictive_lead and reverse_min_p < self.significance,
                "detail": detail,
                "n_samples": len(data),
                "interpretation": "predictive_lead_not_structural_causality",
            }

            self.results = result
            return result

        except Exception as e:
            return {
                "min_p_value": 1.0,
                "best_lag": 0,
                "is_predictive_lead": False,
                "is_causal": False,
                "detail": {},
                "error": str(e),
                "interpretation": "predictive_lead_not_structural_causality",
            }

    def test_causality(
        self,
        social_series: pd.Series,
        sales_series: pd.Series,
        test: str = "ssr_chi2test",
    ) -> dict:
        """Backward-compatible alias for :meth:`test_predictive_lead`."""
        return self.test_predictive_lead(social_series, sales_series, test)

    def multi_product_analysis(
        self,
        df: pd.DataFrame,
        product_col: str = "product_id",
        social_col: str = "social_score",
        sales_col: str = "sales",
        date_col: str = "date",
    ) -> pd.DataFrame:
        """
        多产品批量 Granger 预测领先性分析

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

            gc = self.test_predictive_lead(social, sales)

            results.append(
                {
                    "product_id": product_id,
                    "n_observations": len(group),
                    "social_stationary": social_stationary["is_stationary"],
                    "sales_stationary": sales_stationary["is_stationary"],
                    "is_predictive_lead": gc["is_predictive_lead"],
                    "is_causal": gc["is_predictive_lead"],
                    "min_p_value": gc["min_p_value"],
                    "best_lag": gc["best_lag"],
                    "reverse_predictive_lead": gc.get("reverse_min_p", 1.0) < self.significance,
                    "reverse_causal": gc.get("reverse_min_p", 1.0) < self.significance,
                    "bidirectional": gc.get("is_bidirectional", False),
                }
            )

        return pd.DataFrame(results)

    @staticmethod
    def format_result(result: dict) -> str:
        """格式化分析报告"""
        if "error" in result:
            return f"❌ 分析失败: {result['error']}"

        is_lead = result.get("is_predictive_lead", result.get("is_causal", False))
        status = "✅ 存在显著预测领先性" if is_lead else "❌ 未发现显著预测领先性"
        return (
            f"Granger 预测领先性分析结果（非结构因果）:\n"
            f"  {status}\n"
            f"  最优滞后: {result['best_lag']} 天\n"
            f"  最小 p 值: {result['min_p_value']:.4f}\n"
            f"  样本量: {result['n_samples']}\n"
            f"  反向检验 p: {result.get('reverse_min_p', 'N/A'):.4f}\n"
            f"  双向预测关系: {'是' if result.get('is_bidirectional') else '否'}"
        )


# Compatibility for existing notebooks and integrations. The new name makes
# the statistical interpretation explicit without breaking prior imports.
GrangerCausalAnalyzer = GrangerLeadAnalyzer
