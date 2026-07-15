# 📊 名创优品行业分析报告

> **负责人：队友 C**
> **核心内容：商业模式分析、竞品对标、Granger 因果分析**

---

## 目录

1. [名创优品商业模式分析](./1_商业模式分析.md)
2. [竞品对标：无印良品 / 泡泡玛特 / 完美日记](./2_竞品对标.md)
3. [社媒趋势与销售数据相关性分析](./3_相关性分析.md)
4. [Granger 因果分析报告](./4_Granger因果分析.md)

## 分析流程

```
社媒数据采集 → 时间序列对齐 → 平稳性检验
    ↓
相关性分析 (Pearson/Spearman) → 滞後分析
    ↓
Granger 因果检验 → 结论报告
```

## 🔧 相关代码

```bash
# 运行 Granger 因果分析
python -c "
from src.analysis import GrangerCausalAnalyzer, SocialSalesCorrelation
from src.pipeline.data_generator import generate_social_trend_data

df = generate_social_trend_data()
analyzer = GrangerCausalAnalyzer()
result = analyzer.test_causality(df['social_momentum'], df['sales'])
print(analyzer.format_result(result))
"
```

## 竞品对标框架

| 维度 | 名创优品 | 无印良品 | 泡泡玛特 | 完美日记 |
|------|---------|---------|---------|---------|
| 价格定位 | 10-50元 | 50-500元 | 59-199元 | 30-200元 |
| 目标客群 | Z世代+家庭 | 中产 | 潮流青年 | 年轻女性 |
| SKU数量 | ~8000常新 | ~5000 | ~100 | ~500 |
| 上新周期 | 7-21天 | 月度 | 季度 | 月度 |
| IP策略 | 全球IP联名 | 无IP | 自有IP | KOL联名 |
| 渠道 | 门店+电商 | 门店 | 门店+盲盒 | DTC电商 |
