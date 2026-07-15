"""
模拟数据生成器 (Synthetic Data Generator)
========================================
为回测和展示生成合成名创优品产品数据。

无需真实数据即可演示完整管线。
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def generate_miniso_sample_data(
    n_products: int = 1000,
    n_days: int = 365,
    seed: int = 42,
) -> pd.DataFrame:
    """
    生成合成名创优品产品数据

    Args:
        n_products: 产品总数
        n_days: 时间跨度（天）
        seed: 随机种子

    Returns:
        DataFrame 包含:
        - product_id, date, category, price, social_score
        - is_hit (爆品标签), sales, trend_score, ...
    """
    np.random.seed(seed)

    categories = ["家居", "美妆", "食品", "数码配件", "文具", "玩具", "服饰配件", "香薰"]
    price_tiers = ["低价", "中价", "高价"]
    styles = ["简约", "国潮", "IP联名", "北欧风", "日系", "可爱"]
    materials = ["塑料", "金属", "陶瓷", "布料", "玻璃", "硅胶", "纸张"]

    records = []
    start_date = datetime(2024, 1, 1)

    for i in range(n_products):
        pid = f"MINISO-{i+1:05d}"

        # 产品属性
        category = np.random.choice(categories)
        price_tier = np.random.choice(price_tiers, p=[0.5, 0.35, 0.15])
        style = np.random.choice(styles)
        material = np.random.choice(materials)

        # 基础爆品概率（受品类/风格影响）
        base_hit_prob = 0.08  # 8% 爆品率
        if style == "国潮" or style == "IP联名":
            base_hit_prob += 0.05
        if category == "美妆" or category == "家居":
            base_hit_prob += 0.03
        if price_tier == "高价":
            base_hit_prob -= 0.03

        # 生存周期内每天的数据
        lifespan = np.random.randint(30, 180)  # 30-180天
        for d in range(min(lifespan, n_days)):
            date = start_date + timedelta(days=d)

            # 社媒热度 (随时间波动)
            day_factor = np.sin(2 * np.pi * d / 30) * 0.2 + 0.5
            social_score = np.clip(
                np.random.normal(0.3 + day_factor * 0.5, 0.15), 0, 1
            )

            # 销量（受social_score影响）
            sales = max(0, int(np.random.gamma(2, 50 + social_score * 200)))

            # 爆品标签（全生命周期标记）
            if social_score > 0.75 and sales > 150:
                hit_prob = 0.6
            elif social_score > 0.6 and sales > 80:
                hit_prob = 0.3
            else:
                hit_prob = base_hit_prob

            is_hit = int(np.random.random() < hit_prob)

            # 趋势得分
            trend_score = social_score * 0.7 + day_factor * 0.3

            records.append({
                "product_id": pid,
                "date": date,
                "category": category,
                "price_tier": price_tier,
                "style": style,
                "material": material,
                "social_score": round(social_score, 4),
                "sales": sales,
                "is_hit": is_hit,
                "trend_score": round(trend_score, 4),
                "day_on_market": d + 1,
            })

    df = pd.DataFrame(records)
    print(f"[DataGenerator] 生成 {len(df)} 条记录，{df['product_id'].nunique()} 个产品")
    print(f"  爆品率: {df['is_hit'].mean():.1%}")

    return df


def generate_social_trend_data(n_days: int = 365, seed: int = 42) -> pd.DataFrame:
    """
    生成社媒趋势时间序列数据

    用于 Granger 因果分析演示
    """
    np.random.seed(seed)
    start_date = datetime(2024, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(n_days)]

    # 模拟有因果关系的社媒→销售
    social_momentum = np.random.randn(n_days).cumsum() * 0.1
    social_trend = 0.5 + 0.3 * np.sin(2 * np.pi * np.arange(n_days) / 30) + social_momentum

    # 销售 = lag(social, 3) + noise
    sales = np.roll(social_trend * 200, 3) + np.random.normal(0, 20, n_days)
    sales[:3] = 0  # 前3天无数据（因为lag）

    # 搜索指数、达人笔记数等
    search_index = social_trend * 80 + np.random.normal(0, 5, n_days)
    influencer_notes = social_trend * 50 + np.random.normal(0, 10, n_days)

    df = pd.DataFrame({
        "date": dates,
        "social_momentum": np.clip(social_trend, 0, 1),
        "sales": np.maximum(sales, 0).astype(int),
        "search_index": np.maximum(search_index, 0).astype(int),
        "influencer_notes": np.maximum(influencer_notes, 0).astype(int),
    })

    return df


if __name__ == "__main__":
    df = generate_miniso_sample_data()
    print(df.head())
    print(df.describe())

    social = generate_social_trend_data()
    print(social.head())
