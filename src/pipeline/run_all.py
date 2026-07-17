#!/usr/bin/env python3
"""Run the complete offline demonstration without requiring an LLM service."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import numpy as np

from src.analysis import GrangerLeadAnalyzer, SocialSalesCorrelation
from src.backtest import BacktestConfig, TabularHitPredictor, TimeMachineBacktest
from src.evolution import EvolutionEngine
from src.panel import VirtualPanelCalibrator
from src.pipeline.data_generator import (
    generate_miniso_sample_data,
    generate_social_trend_data,
)


def run_backtest() -> dict:
    data = generate_miniso_sample_data(n_products=1_600, n_days=540, seed=42)
    config = BacktestConfig(min_samples=60)
    engine = TimeMachineBacktest(config)
    result = engine.run(data, TabularHitPredictor(config.random_seed))
    return {
        "evidence_level": "synthetic_demo",
        "completed_windows": len(result.timestamps),
        "average_metrics": result.avg_metrics,
    }


def run_calibration() -> dict:
    rng = np.random.default_rng(42)
    raw_scores = rng.beta(2.2, 4.5, 400)
    observed = np.clip(0.10 + 0.72 * raw_scores + rng.normal(0, 0.09, 400), 0, 1)
    calibrator = VirtualPanelCalibrator(alpha=0.1, random_state=2026)
    calibrator.fit_anchor(raw_scores[:240], observed[:240])
    calibrated, lower, upper = calibrator.predict(raw_scores[240:])
    evaluation = calibrator.evaluate_calibration(raw_scores[240:], observed[240:])
    coverage = float(np.mean((observed[240:] >= lower) & (observed[240:] <= upper)))
    return {
        "evidence_level": "synthetic_demo",
        "ece": evaluation["ece"],
        "interval_coverage": coverage,
        "mean_calibrated_score": float(calibrated.mean()),
        "fit_diagnostics": calibrator.fit_diagnostics,
    }


def run_evolution() -> dict:
    templates = [
        {
            "category": "家居",
            "price_tier": "中价",
            "style": "国潮",
            "target_audience": "Z世代",
            "material": "陶瓷",
            "features": ["便携", "礼盒装"],
        },
        {
            "category": "美妆",
            "price_tier": "低价",
            "style": "可爱",
            "target_audience": "学生",
            "material": "塑料",
            "features": ["便携", "卡通IP"],
        },
    ]
    attribute_pool = {
        "categories": ["家居", "美妆", "食品", "数码配件", "文具", "玩具", "香薰"],
        "price_tiers": ["低价", "中价", "高价"],
        "styles": ["简约", "国潮", "IP联名", "日系", "可爱"],
        "audiences": ["Z世代", "学生", "白领", "亲子"],
        "materials": ["塑料", "金属", "陶瓷", "布料", "玻璃", "硅胶", "纸张"],
        "features": ["便携", "IP联名", "环保", "多功能", "礼盒装", "限量版", "防水"],
    }
    engine = EvolutionEngine(population_size=40, n_generations=12, random_state=2026)
    front = engine.run(templates, attribute_pool)
    return {
        "evidence_level": "algorithm_demo",
        "pareto_size": len(front),
        "top_concepts": [
            {
                "id": idea.id,
                "concept": idea.to_prompt(),
                "objectives": {
                    "demand": idea.hit_score,
                    "dfm": idea.dfm_score,
                    "novelty": idea.novelty_score,
                },
            }
            for idea in front[:5]
        ],
    }


def run_granger() -> dict:
    data = generate_social_trend_data(n_days=300, seed=42)
    analyzer = GrangerLeadAnalyzer(max_lag=7)
    result = analyzer.test_predictive_lead(data["social_momentum"], data["sales"])
    lag_corr = SocialSalesCorrelation().lag_correlation(
        data["social_momentum"], data["sales"], max_lag=7
    )
    return {
        "evidence_level": "synthetic_demo",
        "granger": result,
        "lag_correlation": lag_corr,
    }


def main() -> None:
    print("MINISO AI Product Decision Engine | offline demonstration")
    print("Evidence level: synthetic/algorithm demo; no production KPI claims")
    results = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "backtest": run_backtest(),
        "calibration": run_calibration(),
        "evolution": run_evolution(),
        "lead_signal": run_granger(),
    }
    print(
        json.dumps(
            results,
            ensure_ascii=False,
            indent=2,
            default=lambda value: value.item() if isinstance(value, np.generic) else str(value),
        )
    )


if __name__ == "__main__":
    main()
