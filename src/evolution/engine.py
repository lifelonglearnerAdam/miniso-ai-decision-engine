"""
进化式创意引擎 (Evolutionary Creative Engine)
===========================================
创新4: 遗传算法驱动的产品创意进化

核心流程:
  1. 种群初始化: 基于趋势生成初始创意
  2. 适应度评估: 多目标 (爆品概率 + DFM可行性)
  3. 选择/交叉/变异: 帕累托前沿优化
  4. 偏好飞轮: 用户反馈驱动进化方向
"""

import numpy as np
from typing import Optional, Callable
from dataclasses import dataclass, field


@dataclass
class ProductIdea:
    """产品创意基因型"""
    id: str
    category: str           # 品类 (如: 家居/美妆/食品)
    price_tier: str         # 价格带 (低价/中价/高价)
    style: str              # 风格 (简约/IP联名/国潮)
    target_audience: str    # 目标人群
    material: str           # 材质
    features: list[str]     # 特征列表
    dfm_score: float = 1.0  # 可制造性评分

    def to_prompt(self) -> str:
        """转 LLM prompt"""
        return (
            f"品类: {self.category}, 价格带: {self.price_tier}, "
            f"风格: {self.style}, 受众: {self.target_audience}, "
            f"材质: {self.material}, 特征: {', '.join(self.features)}"
        )


@dataclass
class DFMRule:
    """可制造性约束规则"""
    condition: str          # 条件描述
    penalty: float          # 违反惩罚 (0~1)
    description: str        # 规则描述


class DFMConstraintEngine:
    """DFM 可制造性约束引擎"""

    def __init__(self):
        self.rules: list[DFMRule] = self._default_rules()

    def _default_rules(self) -> list[DFMRule]:
        return [
            DFMRule("material in ['钛合金','纯金']", 0.6, "贵金属/稀有材料成本过高"),
            DFMRule("features contains 'OLED' and price_tier == '低价'", 0.7, "低价产品无法承载OLED屏"),
            DFMRule("category == '电子产品' and features contains '防水'", 0.3, "防水需要额外密封工艺"),
            DFMRule("price_tier == '高价' and len(features) < 3", 0.4, "高价产品应有足够卖点"),
            DFMRule("category == '食品' and material == '塑料'", 0.8, "食品接触禁用非食品级塑料"),
            DFMRule("style == 'IP联名' and price_tier == '低价'", 0.3, "IP联名定价空间有限"),
        ]

    def add_rule(self, rule: DFMRule):
        self.rules.append(rule)

    def evaluate(self, idea: ProductIdea) -> float:
        """
        评估可制造性得分 (0~1, 越高越可行)
        """
        score = 1.0
        idea_str = idea.to_prompt()

        for rule in self.rules:
            # 简化规则匹配 (实际可用更复杂的规则引擎)
            keywords = rule.condition.lower()
            if any(kw in idea_str.lower() for kw in keywords.split("==")):
                score -= rule.penalty

        return max(0.0, score)


class PreferenceFlyingWheel:
    """
    偏好飞轮 (Preference Flying Wheel)
    通过用户反馈持续调整进化方向
    """

    def __init__(self, n_attributes: int = 5):
        self.weights = np.ones(n_attributes) / n_attributes
        self.history: list[dict] = []

    def update(self, feedback: dict[str, float]):
        """
        根据反馈更新偏好权重

        Args:
            feedback: {"attribute": score, ...}
        """
        self.history.append(feedback)

        # 指数移动平均更新权重
        lr = 0.3
        for attr, score in feedback.items():
            idx = hash(attr) % len(self.weights)
            self.weights[idx] = (1 - lr) * self.weights[idx] + lr * score

        self.weights /= self.weights.sum()

    def get_weights(self) -> np.ndarray:
        return self.weights


class EvolutionEngine:
    """
    进化式创意引擎

    使用遗传算法搜索最优产品创意组合。
    """

    def __init__(
        self,
        population_size: int = 100,
        mutation_rate: float = 0.2,
        crossover_rate: float = 0.7,
        n_generations: int = 50,
    ):
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.n_generations = n_generations

        self.population: list[ProductIdea] = []
        self.history: dict[int, list[float]] = {}
        self.dfm_engine = DFMConstraintEngine()
        self.flying_wheel = PreferenceFlyingWheel()

    def initialize_population(self, templates: list[dict]):
        """从模板初始化种群"""
        self.population = []
        for i, t in enumerate(templates):
            idea = ProductIdea(
                id=f"gen0_{i}",
                category=t.get("category", "家居"),
                price_tier=t.get("price_tier", "中价"),
                style=t.get("style", "简约"),
                target_audience=t.get("target_audience", "Z世代"),
                material=t.get("material", "塑料"),
                features=t.get("features", ["便携"]),
            )
            idea.dfm_score = self.dfm_engine.evaluate(idea)
            self.population.append(idea)

    def evaluate(self, idea: ProductIdea, score_fn: Optional[Callable] = None) -> float:
        """
        评估适应度

        score_fn: LLM 评分函数 (返回爆品概率)
        """
        if score_fn:
            hit_prob = score_fn(idea.to_prompt())
        else:
            # 默认: 综合 DFM + 随机变异
            hit_prob = 0.3 + 0.4 * idea.dfm_score + 0.3 * np.random.random()

        # 飞轮加权
        weights = self.flying_wheel.get_weights()
        diversity = np.std([hash(idea.to_prompt()) % 100 for _ in range(3)]) / 100

        return 0.5 * hit_prob + 0.3 * idea.dfm_score + 0.2 * diversity

    def select(self, fitness: list[float]) -> list[ProductIdea]:
        """锦标赛选择"""
        selected = []
        k = 3  # 锦标赛大小

        for _ in range(self.population_size):
            idx = np.random.choice(len(self.population), k, replace=False)
            winner = idx[np.argmax([fitness[i] for i in idx])]
            selected.append(self.population[winner])

        return selected

    def crossover(self, parent1: ProductIdea, parent2: ProductIdea) -> ProductIdea:
        """单点交叉"""
        if np.random.random() > self.crossover_rate:
            return parent1

        child = ProductIdea(
            id=f"child_{np.random.randint(10000)}",
            category=parent1.category if np.random.random() > 0.5 else parent2.category,
            price_tier=parent1.price_tier if np.random.random() > 0.5 else parent2.price_tier,
            style=parent1.style if np.random.random() > 0.5 else parent2.style,
            target_audience=parent1.target_audience if np.random.random() > 0.5 else parent2.target_audience,
            material=parent1.material if np.random.random() > 0.5 else parent2.material,
            features=np.random.choice(parent1.features, len(parent1.features)).tolist(),
        )

        child.dfm_score = self.dfm_engine.evaluate(child)
        return child

    def mutate(self, idea: ProductIdea, attribute_pool: dict) -> ProductIdea:
        """变异"""
        if np.random.random() > self.mutation_rate:
            return idea

        mutated = ProductIdea(
            id=idea.id,
            category=np.random.choice(attribute_pool.get("categories", [idea.category])),
            price_tier=np.random.choice(attribute_pool.get("price_tiers", [idea.price_tier])),
            style=np.random.choice(attribute_pool.get("styles", [idea.style])),
            target_audience=np.random.choice(attribute_pool.get("audiences", [idea.target_audience])),
            material=np.random.choice(attribute_pool.get("materials", [idea.material])),
            features=idea.features.copy(),
        )

        if np.random.random() > 0.5 and attribute_pool.get("features"):
            mutated.features = np.random.choice(
                attribute_pool["features"],
                min(len(idea.features) + 1, 5),
                replace=False,
            ).tolist()

        mutated.dfm_score = self.dfm_engine.evaluate(mutated)
        return mutated

    def run(
        self,
        templates: list[dict],
        attribute_pool: dict,
        score_fn: Optional[Callable] = None,
    ) -> list[ProductIdea]:
        """
        运行进化循环

        Args:
            templates: 初始种群模板
            attribute_pool: 变异属性池
            score_fn: 评分函数

        Returns:
            帕累托最优创意列表
        """
        self.initialize_population(templates)

        for gen in range(self.n_generations):
            # 评估
            fitness = [self.evaluate(ind, score_fn) for ind in self.population]

            # 记录
            self.history[gen] = fitness

            # 选择
            selected = self.select(fitness)

            # 交叉 + 变异
            new_population = []
            for i in range(0, self.population_size, 2):
                p1, p2 = selected[i], selected[(i + 1) % len(selected)]
                child = self.crossover(p1, p2)
                child = self.mutate(child, attribute_pool)
                new_population.append(child)

            # 精英保留
            elite_idx = np.argsort(fitness)[-5:]
            for idx in elite_idx:
                new_population[np.random.randint(len(new_population))] = self.population[idx]

            self.population = new_population

            if gen % 10 == 0:
                print(f"进化 [{gen}/{self.n_generations}] 平均适应度: {np.mean(fitness):.4f}")

        # 返回最终种群 (按适应度排序)
        final_fitness = [self.evaluate(ind, score_fn) for ind in self.population]
        best_idx = np.argsort(final_fitness)[::-1]
        pareto_front = [self.population[i] for i in best_idx[:20]]

        return pareto_front
