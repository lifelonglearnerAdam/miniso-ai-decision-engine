# 🧬 进化式创意引擎设计文档

> **负责人：队友 A + B + C**
> **核心内容：进化循环参数、DFM 可制造性约束规则库**

---

## 进化算法参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 种群大小 | 100 | 每代创意数量 |
| 变异率 | 0.2 | 基因变异概率 |
| 交叉率 | 0.7 | 基因交叉概率 |
| 进化代数 | 50 | 迭代次数 |
| 精英保留 | 5 | 每代保留最优个体数 |

## 产品基因结构

```
ProductIdea:
  ├── category: str          (品类)
  ├── price_tier: str        (价格带)
  ├── style: str             (风格)
  ├── target_audience: str   (目标人群)
  ├── material: str          (材质)
  └── features: list[str]    (特征列表)
```

## DFM 约束规则库

> 规则由队友 C 主导建立

### 已有规则

| 条件 | 惩罚分 | 说明 |
|------|--------|------|
| 贵金属/稀有材料 | 0.6 | 成本过高 |
| 低价+OLED特性 | 0.7 | 成本倒挂 |
| 电子产品+防水 | 0.3 | 需要密封工艺 |
| 高价+不足3特征 | 0.4 | 卖点不足 |
| 食品+塑料 | 0.8 | 安全合规 |
| IP联名+低价 | 0.3 | 定价空间有限 |

### 扩展建议

队友 C 可在 `src/evolution/engine.py` 的 `DFMConstraintEngine._default_rules()` 中添加更多规则。

## 偏好飞轮

```
用户反馈 → 更新权重 → 调整进化方向 → 生成新创意 → 再次收集反馈
```

## 运行演示

```bash
python -c "
from src.evolution import EvolutionEngine, DFMConstraintEngine

engine = EvolutionEngine(population_size=50, n_generations=20)
templates = [
    {'category': '家居', 'style': '国潮', 'price_tier': '中价',
     'target_audience': 'Z世代', 'material': '陶瓷', 'features': ['故宫联名']},
]
attribute_pool = {
    'categories': ['家居', '美妆', '食品', '玩具'],
    'styles': ['简约', '国潮', 'IP联名', '可爱'],
    'price_tiers': ['低价', '中价', '高价'],
    'audiences': ['Z世代', '学生', '白领'],
    'materials': ['塑料', '金属', '陶瓷', '布料'],
    'features': ['便携', 'IP联名', '环保', '多功能'],
}
front = engine.run(templates, attribute_pool)
for i, idea in enumerate(front[:5]):
    print(f'{i+1}. {idea}')
"
```
