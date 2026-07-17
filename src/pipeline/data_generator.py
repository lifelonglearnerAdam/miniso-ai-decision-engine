"""Deterministic synthetic data for local demos and automated tests.

The generated rows represent *product decisions*, not daily observations.  All
features are available at the decision date; ``is_hit`` and ``sales_90d`` are
future outcomes.  This separation makes the leakage contract visible and lets
the time-machine backtest remove outcome columns before scoring candidates.

Synthetic data is not evidence of real MINISO performance.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def _sigmoid(value: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-value))


def generate_miniso_sample_data(
    n_products: int = 1_200,
    n_days: int = 540,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate one leakage-auditable row per product decision.

    ``social_score`` and ``trend_score`` are pre-launch signals.  The outcome
    fields are sampled from a latent response model and are intentionally
    retained so tests can verify that the evaluator hides them from predictors.
    """
    if n_products <= 0 or n_days <= 0:
        raise ValueError("n_products and n_days must be positive")

    rng = np.random.default_rng(seed)
    categories = np.array(["家居", "美妆", "食品", "数码配件", "文具", "玩具", "服饰配件", "香薰"])
    price_tiers = np.array(["低价", "中价", "高价"])
    styles = np.array(["简约", "国潮", "IP联名", "北欧风", "日系", "可爱"])
    materials = np.array(["塑料", "金属", "陶瓷", "布料", "玻璃", "硅胶", "纸张"])

    day_offsets = rng.integers(0, n_days, size=n_products)
    category = rng.choice(categories, size=n_products)
    price_tier = rng.choice(price_tiers, size=n_products, p=[0.50, 0.36, 0.14])
    style = rng.choice(styles, size=n_products)
    material = rng.choice(materials, size=n_products)

    seasonal = 0.5 + 0.5 * np.sin(2 * np.pi * day_offsets / 90)
    social_score = np.clip(rng.beta(2.2, 3.8, size=n_products) + 0.12 * seasonal, 0, 1)
    trend_score = np.clip(
        0.68 * social_score + 0.20 * seasonal + rng.normal(0, 0.08, n_products),
        0,
        1,
    )

    tier_price = {"低价": 19.9, "中价": 49.9, "高价": 99.0}
    price = np.array([tier_price[tier] for tier in price_tier])
    price *= rng.lognormal(mean=0, sigma=0.16, size=n_products)
    cost_ratio = np.where(price_tier == "低价", 0.44, np.where(price_tier == "中价", 0.38, 0.34))
    estimated_unit_cost = price * np.clip(rng.normal(cost_ratio, 0.04), 0.20, 0.65)

    latent = (
        -2.80
        + 2.35 * social_score
        + 1.05 * trend_score
        + 0.58 * np.isin(style, ["国潮", "IP联名"])
        + 0.34 * np.isin(category, ["美妆", "家居", "玩具"])
        - 0.40 * (price_tier == "高价")
        + 0.18 * seasonal
    )
    hit_probability = _sigmoid(latent)
    is_hit = rng.binomial(1, hit_probability)

    sales_scale = 420 + 1_800 * hit_probability + 900 * is_hit
    sales_90d = np.maximum(0, rng.lognormal(np.log(sales_scale), 0.36)).astype(int)
    realized_margin = np.maximum(0, (price - estimated_unit_cost) * sales_90d)

    start_date = datetime(2024, 1, 1)
    frame = pd.DataFrame(
        {
            "product_id": [f"DEMO-{idx + 1:05d}" for idx in range(n_products)],
            "date": [start_date + timedelta(days=int(offset)) for offset in day_offsets],
            "category": category,
            "price_tier": price_tier,
            "style": style,
            "material": material,
            "price": np.round(price, 2),
            "estimated_unit_cost": np.round(estimated_unit_cost, 2),
            "social_score": np.round(social_score, 4),
            "trend_score": np.round(trend_score, 4),
            "is_hit": is_hit.astype(int),
            "sales_90d": sales_90d,
            "realized_margin": np.round(realized_margin, 2),
            "data_provenance": "synthetic-demo-v2",
        }
    )
    return frame.sort_values(["date", "product_id"]).reset_index(drop=True)


def generate_social_trend_data(n_days: int = 365, seed: int = 42) -> pd.DataFrame:
    """Generate a stationary-ish leading signal and a lagged sales response."""
    if n_days < 30:
        raise ValueError("n_days must be at least 30")
    rng = np.random.default_rng(seed)
    start_date = datetime(2024, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(n_days)]

    time = np.arange(n_days)
    social_trend = 0.50 + 0.20 * np.sin(2 * np.pi * time / 30) + rng.normal(0, 0.07, n_days)
    social_trend = np.clip(social_trend, 0, 1)
    lag = 3
    lagged_social = np.concatenate([np.repeat(social_trend[0], lag), social_trend[:-lag]])
    sales = 80 + 260 * lagged_social + rng.normal(0, 18, n_days)

    return pd.DataFrame(
        {
            "date": dates,
            "social_momentum": social_trend,
            "sales": np.maximum(sales, 0).astype(int),
            "search_index": np.maximum(100 * social_trend + rng.normal(0, 5, n_days), 0).astype(
                int
            ),
            "influencer_notes": np.maximum(55 * social_trend + rng.normal(0, 7, n_days), 0).astype(
                int
            ),
        }
    )


if __name__ == "__main__":
    demo = generate_miniso_sample_data()
    print(demo.head())
    print(f"rows={len(demo)}, synthetic hit rate={demo['is_hit'].mean():.1%}")
