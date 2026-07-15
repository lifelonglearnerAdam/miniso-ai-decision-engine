#!/usr/bin/env python3
"""
名创优品 AI 决策引擎 — 完整执行管线
====================================
在 RTX 4090 上运行完整的：回测 → 校准 → 进化 → Agent 管线。
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from datetime import datetime

from src.backtest import TimeMachineBacktest, BacktestConfig
from src.panel import VirtualPanelCalibrator
from src.evolution import EvolutionEngine
from src.analysis import GrangerCausalAnalyzer, SocialSalesCorrelation
from src.pipeline.data_generator import generate_miniso_sample_data, generate_social_trend_data


def run_backtest():
    """运行时光机回测"""
    print("\n" + "=" * 60)
    print("📊 1/4 时光机回测")
    print("=" * 60)

    data = generate_miniso_sample_data(n_products=500, n_days=365)

    config = BacktestConfig(
        train_window=180,
        gap_days=14,
        pred_window=90,
        stride=30,
    )

    backtest = TimeMachineBacktest(config)

    # 智能预测器（比随机好一些）
    def smart_predictor(train_df, pred_df):
        scores = []
        for _, row in pred_df.iterrows():
            base = 0.1
            if row.get("social_score", 0) > 0.7:
                base += 0.3
            if row.get("style") in ["国潮", "IP联名"]:
                base += 0.15
            if row.get("category") in ["美妆", "家居"]:
                base += 0.1
            if row.get("day_on_market", 30) < 7:
                base -= 0.1
            scores.append(min(base + np.random.random() * 0.2, 1.0))
        return np.array(scores)

    # 随机基线
    random_results = backtest.run(data, backtest.random_baseline)
    smart_results = backtest.run(data, smart_predictor)

    print("\n📈 随机基线:")
    print(backtest.summary(random_results))

    print("\n📈 AI 智能预测:")
    print(backtest.summary(smart_results))

    # 对比
    print("\n⚡ 提升 vs 基线:")
    for key in smart_results.avg_metrics:
        if key in random_results.avg_metrics and random_results.avg_metrics[key] > 0:
            lift = (smart_results.avg_metrics[key] - random_results.avg_metrics[key]) / random_results.avg_metrics[key]
            print(f"  {key}: {smart_results.avg_metrics[key]:.4f} vs {random_results.avg_metrics[key]:.4f} (↑{lift:.1%})")

    return smart_results, random_results


def run_calibration():
    """运行虚拟面板校准演示"""
    print("\n" + "=" * 60)
    print("🎯 2/4 虚拟面板校准")
    print("=" * 60)

    np.random.seed(42)

    # 模拟 LLM 评分
    n_samples = 200
    llm_scores = np.random.beta(2, 5, n_samples)  # LLM 有偏评分
    true_scores = llm_scores * 0.7 + np.random.normal(0, 0.1, n_samples)  # 真实评分
    true_scores = np.clip(true_scores, 0, 1)

    # 切分校准集/测试集
    n_calib = 50
    llm_calib, llm_test = llm_scores[:n_calib], llm_scores[n_calib:]
    true_calib, true_test = true_scores[:n_calib], true_scores[n_calib:]

    # 校准
    calibrator = VirtualPanelCalibrator(alpha=0.1)
    calibrator.fit_anchor(llm_calib, true_calib)

    # 预测
    calib, lower, upper = calibrator.predict(llm_test)

    # 评估
    eval_result = calibrator.evaluate_calibration(llm_test, true_test)
    print(f"\n📊 校准评估:")
    print(f"  ACE (平均校准误差): {eval_result['ace']:.4f}")
    print(f"  样本量: {eval_result['n_samples']}")

    # 置信区间覆盖率
    coverage = np.mean((true_test >= lower) & (true_test <= upper))
    print(f"  90% 置信区间覆盖率: {coverage:.1%}")

    return calibrator


def run_evolution():
    """运行进化引擎演示"""
    print("\n" + "=" * 60)
    print("🧬 3/4 进化式创意引擎")
    print("=" * 60)

    engine = EvolutionEngine(
        population_size=50,
        mutation_rate=0.2,
        crossover_rate=0.7,
        n_generations=20,
    )

    templates = [
        {"category": "家居", "price_tier": "中价", "style": "国潮",
         "target_audience": "Z世代", "material": "陶瓷",
         "features": ["故宫联名", "茶具"]},
        {"category": "美妆", "price_tier": "低价", "style": "可爱",
         "target_audience": "学生", "material": "塑料",
         "features": ["便携", "卡通IP"]},
        {"category": "食品", "price_tier": "低价", "style": "日系",
         "target_audience": "白领", "material": "纸张",
         "features": ["健康", "小包装"]},
    ]

    attribute_pool = {
        "categories": ["家居", "美妆", "食品", "数码配件", "文具", "玩具", "服饰配件", "香薰"],
        "price_tiers": ["低价", "中价", "高价"],
        "styles": ["简约", "国潮", "IP联名", "北欧风", "日系", "可爱"],
        "audiences": ["Z世代", "学生", "白领", "亲子", "银发族"],
        "materials": ["塑料", "金属", "陶瓷", "布料", "玻璃", "硅胶", "纸张", "竹木"],
        "features": ["便携", "IP联名", "环保", "多功能", "礼盒装", "限量版", "智能"],
    }

    pareto_front = engine.run(templates, attribute_pool)

    print(f"\n🏆 帕累托最优创意 (Top-5):")
    for i, idea in enumerate(pareto_front[:5]):
        print(f"  {i+1}. [{idea.category}] {idea.style} - {idea.target_audience}")
        print(f"     材质: {idea.material}, 特征: {', '.join(idea.features)}")
        print(f"     DFM评分: {idea.dfm_score:.2f}")

    return engine


def run_granger():
    """运行 Granger 因果分析演示"""
    print("\n" + "=" * 60)
    print("🔗 4/4 Granger 因果分析")
    print("=" * 60)

    df = generate_social_trend_data(n_days=200)

    analyzer = GrangerCausalAnalyzer(max_lag=7)

    # 平稳性
    social_stat = analyzer.check_stationarity(df["social_momentum"], "社媒热度")
    sales_stat = analyzer.check_stationarity(df["sales"], "销量")
    print(f"\n  社媒平稳: {social_stat['is_stationary']} (p={social_stat['p_value']:.4f})")
    print(f"  销量平稳: {sales_stat['is_stationary']} (p={sales_stat['p_value']:.4f})")

    # 因果检验
    social = df["social_momentum"]
    sales = df["sales"]
    if not social_stat["is_stationary"]:
        social = analyzer.make_stationary(social)
    if not sales_stat["is_stationary"]:
        sales = analyzer.make_stationary(sales)

    result = analyzer.test_causality(social, sales)
    print(f"\n  {analyzer.format_result(result)}")

    # 相关性
    corr = SocialSalesCorrelation()
    pearson = corr.pearson_correlation(df["social_momentum"], df["sales"])
    print(f"\n  Pearson 相关: r={pearson['pearson_r']:.3f}, p={pearson['pearson_p']:.4f}")

    return result


def main():
    """主入口：按顺序运行所有模块"""
    print("🚀 名创优品 AI 决策引擎 — 完整管线")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("💻 推理引擎: Ollama (Qwen2.5) on RTX 4090")

    results = {}

    try:
        results["backtest"] = run_backtest()
    except Exception as e:
        print(f"❌ 回测失败: {e}")

    try:
        results["calibration"] = run_calibration()
    except Exception as e:
        print(f"❌ 校准失败: {e}")

    try:
        results["evolution"] = run_evolution()
    except Exception as e:
        print(f"❌ 进化失败: {e}")

    try:
        results["granger"] = run_granger()
    except Exception as e:
        print(f"❌ Granger 失败: {e}")

    print("\n" + "=" * 60)
    print("✅ 管线执行完成！")
    print(f"⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    return results


if __name__ == "__main__":
    main()
