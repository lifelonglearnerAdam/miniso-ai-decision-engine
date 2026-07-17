"""Multi-objective evolutionary search for product concepts.

The implementation keeps three objectives separate: predicted demand,
manufacturability and novelty.  The returned front is non-dominated; it is not
a relabelled single-score ranking.
"""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass

import numpy as np


@dataclass
class ProductIdea:
    """A product concept encoded as a compact, mutable genotype."""

    id: str
    category: str
    price_tier: str
    style: str
    target_audience: str
    material: str
    features: list[str]
    dfm_score: float = 1.0
    hit_score: float = 0.0
    novelty_score: float = 0.0

    def to_prompt(self) -> str:
        return (
            f"品类: {self.category}, 价格带: {self.price_tier}, "
            f"风格: {self.style}, 受众: {self.target_audience}, "
            f"材质: {self.material}, 特征: {', '.join(self.features)}"
        )

    @property
    def objectives(self) -> tuple[float, float, float]:
        return self.hit_score, self.dfm_score, self.novelty_score


@dataclass(frozen=True)
class DFMRule:
    """A human-readable manufacturing constraint."""

    rule_id: str
    penalty: float
    description: str


class DFMConstraintEngine:
    """Evaluate explicit, auditable design-for-manufacturing rules."""

    rules = (
        DFMRule("rare_material", 0.60, "稀有或贵金属不符合大众价格带"),
        DFMRule("low_price_oled", 0.70, "低价产品搭载 OLED 存在成本倒挂风险"),
        DFMRule("electronics_waterproof", 0.30, "电子产品防水需要额外密封与测试"),
        DFMRule("premium_thin_value", 0.40, "高价概念缺少足够价值点"),
        DFMRule("food_contact_plastic", 0.45, "食品接触塑料需要材料合规证明"),
        DFMRule("low_price_ip", 0.30, "低价 IP 联名需核验授权费空间"),
    )

    @staticmethod
    def _violated_rule_ids(idea: ProductIdea) -> list[str]:
        features = {feature.upper() for feature in idea.features}
        violations = []
        if idea.material in {"钛合金", "纯金"}:
            violations.append("rare_material")
        if "OLED" in features and idea.price_tier == "低价":
            violations.append("low_price_oled")
        if idea.category in {"电子产品", "数码配件"} and "防水" in idea.features:
            violations.append("electronics_waterproof")
        if idea.price_tier == "高价" and len(set(idea.features)) < 3:
            violations.append("premium_thin_value")
        if idea.category == "食品" and idea.material == "塑料":
            violations.append("food_contact_plastic")
        if idea.style == "IP联名" and idea.price_tier == "低价":
            violations.append("low_price_ip")
        return violations

    def evaluate_with_reasons(self, idea: ProductIdea) -> tuple[float, list[DFMRule]]:
        violated = set(self._violated_rule_ids(idea))
        matched = [rule for rule in self.rules if rule.rule_id in violated]
        # Multiplicative penalties avoid instantly collapsing a concept to zero.
        score = float(np.prod([1.0 - rule.penalty for rule in matched])) if matched else 1.0
        return max(0.0, min(1.0, score)), matched

    def evaluate(self, idea: ProductIdea) -> float:
        return self.evaluate_with_reasons(idea)[0]


class PreferenceFlyingWheel:
    """A deterministic preference-weight accumulator for human feedback."""

    attributes = ("demand", "dfm", "novelty")

    def __init__(self):
        self.weights = np.array([0.50, 0.30, 0.20], dtype=float)
        self.history: list[dict[str, float]] = []

    def update(self, feedback: dict[str, float]) -> None:
        unknown = set(feedback) - set(self.attributes)
        if unknown:
            raise ValueError(f"unknown preference attributes: {sorted(unknown)}")
        self.history.append(dict(feedback))
        learning_rate = 0.30
        for name, score in feedback.items():
            if not 0 <= score <= 1:
                raise ValueError("preference scores must be between 0 and 1")
            index = self.attributes.index(name)
            self.weights[index] = (1 - learning_rate) * self.weights[index] + learning_rate * score
        self.weights /= self.weights.sum()

    def get_weights(self) -> np.ndarray:
        return self.weights.copy()


def _dominates(left: ProductIdea, right: ProductIdea) -> bool:
    return all(a >= b for a, b in zip(left.objectives, right.objectives, strict=True)) and any(
        a > b for a, b in zip(left.objectives, right.objectives, strict=True)
    )


class EvolutionEngine:
    """Run a reproducible evolutionary loop and return a Pareto front."""

    def __init__(
        self,
        population_size: int = 100,
        mutation_rate: float = 0.20,
        crossover_rate: float = 0.70,
        n_generations: int = 50,
        random_state: int = 2026,
    ):
        if population_size < 4:
            raise ValueError("population_size must be at least 4")
        if not 0 <= mutation_rate <= 1 or not 0 <= crossover_rate <= 1:
            raise ValueError("mutation_rate and crossover_rate must be in [0, 1]")
        if n_generations <= 0:
            raise ValueError("n_generations must be positive")
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.n_generations = n_generations
        self.rng = np.random.default_rng(random_state)
        self.population: list[ProductIdea] = []
        self.history: dict[int, dict[str, float]] = {}
        self.dfm_engine = DFMConstraintEngine()
        self.flying_wheel = PreferenceFlyingWheel()
        self._counter = 0

    def _next_id(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}_{self._counter:06d}"

    @staticmethod
    def _from_template(template: dict, idea_id: str) -> ProductIdea:
        return ProductIdea(
            id=idea_id,
            category=template.get("category", "家居"),
            price_tier=template.get("price_tier", "中价"),
            style=template.get("style", "简约"),
            target_audience=template.get("target_audience", "Z世代"),
            material=template.get("material", "塑料"),
            features=list(template.get("features", ["便携"])),
        )

    def initialize_population(self, templates: list[dict], attribute_pool: dict) -> None:
        if not templates:
            raise ValueError("at least one template is required")
        self.population = []
        for index in range(self.population_size):
            base = self._from_template(templates[index % len(templates)], self._next_id("gen0"))
            if index >= len(templates):
                base = self.mutate(base, attribute_pool, force=True)
            base.dfm_score = self.dfm_engine.evaluate(base)
            self.population.append(base)

    def _novelty(self, idea: ProductIdea, population: list[ProductIdea]) -> float:
        signatures = [
            {
                item.category,
                item.price_tier,
                item.style,
                item.target_audience,
                item.material,
                *item.features,
            }
            for item in population
            if item.id != idea.id
        ]
        if not signatures:
            return 1.0
        target = {
            idea.category,
            idea.price_tier,
            idea.style,
            idea.target_audience,
            idea.material,
            *idea.features,
        }
        similarities = [len(target & other) / len(target | other) for other in signatures]
        nearest_similarity = max(similarities)
        return float(np.clip(1.0 - nearest_similarity, 0, 1))

    def score_population(
        self,
        score_fn: Callable[[str], float] | None = None,
    ) -> list[float]:
        composite_scores = []
        weights = self.flying_wheel.get_weights()
        for idea in self.population:
            idea.dfm_score = self.dfm_engine.evaluate(idea)
            if score_fn is not None:
                idea.hit_score = float(np.clip(score_fn(idea.to_prompt()), 0, 1))
            else:
                # Transparent heuristic for an offline demo; production injects a model.
                idea.hit_score = float(
                    np.clip(
                        0.30
                        + 0.18 * (idea.style in {"国潮", "IP联名"})
                        + 0.12 * (idea.category in {"家居", "美妆", "玩具"})
                        + 0.08 * min(len(set(idea.features)), 4)
                        - 0.10 * (idea.price_tier == "高价"),
                        0,
                        1,
                    )
                )
            idea.novelty_score = self._novelty(idea, self.population)
            composite_scores.append(float(np.dot(weights, idea.objectives)))
        return composite_scores

    def select(self, fitness: list[float]) -> list[ProductIdea]:
        if len(fitness) != len(self.population):
            raise ValueError("fitness must align with population")
        selected = []
        tournament_size = min(3, len(self.population))
        for _ in range(self.population_size):
            candidates = self.rng.choice(len(self.population), tournament_size, replace=False)
            winner = max(candidates, key=lambda index: fitness[int(index)])
            selected.append(self.population[int(winner)])
        return selected

    def crossover(self, parent1: ProductIdea, parent2: ProductIdea) -> ProductIdea:
        if self.rng.random() > self.crossover_rate:
            child = deepcopy(parent1)
            child.id = self._next_id("clone")
            return child
        feature_pool = list(dict.fromkeys(parent1.features + parent2.features))
        n_features = max(
            1, min(len(feature_pool), round((len(parent1.features) + len(parent2.features)) / 2))
        )
        chosen_features = self.rng.choice(feature_pool, n_features, replace=False).tolist()
        child = ProductIdea(
            id=self._next_id("child"),
            category=self.rng.choice([parent1.category, parent2.category]),
            price_tier=self.rng.choice([parent1.price_tier, parent2.price_tier]),
            style=self.rng.choice([parent1.style, parent2.style]),
            target_audience=self.rng.choice([parent1.target_audience, parent2.target_audience]),
            material=self.rng.choice([parent1.material, parent2.material]),
            features=chosen_features,
        )
        child.dfm_score = self.dfm_engine.evaluate(child)
        return child

    def mutate(self, idea: ProductIdea, attribute_pool: dict, force: bool = False) -> ProductIdea:
        mutated = deepcopy(idea)
        mutated.id = self._next_id("mutant")
        if not force and self.rng.random() > self.mutation_rate:
            return mutated

        fields = [
            ("category", "categories"),
            ("price_tier", "price_tiers"),
            ("style", "styles"),
            ("target_audience", "audiences"),
            ("material", "materials"),
        ]
        attribute, pool_key = fields[int(self.rng.integers(0, len(fields)))]
        pool = list(attribute_pool.get(pool_key, [getattr(mutated, attribute)]))
        if pool:
            setattr(mutated, attribute, str(self.rng.choice(pool)))

        if attribute_pool.get("features") and (force or self.rng.random() < 0.6):
            feature_pool = list(dict.fromkeys(attribute_pool["features"]))
            target_size = min(
                max(1, len(mutated.features) + int(self.rng.choice([-1, 0, 1]))),
                min(5, len(feature_pool)),
            )
            mutated.features = self.rng.choice(feature_pool, target_size, replace=False).tolist()
        mutated.dfm_score = self.dfm_engine.evaluate(mutated)
        return mutated

    @staticmethod
    def pareto_front(population: list[ProductIdea]) -> list[ProductIdea]:
        return [
            candidate
            for candidate in population
            if not any(
                other.id != candidate.id and _dominates(other, candidate) for other in population
            )
        ]

    def run(
        self,
        templates: list[dict],
        attribute_pool: dict,
        score_fn: Callable[[str], float] | None = None,
    ) -> list[ProductIdea]:
        self.initialize_population(templates, attribute_pool)
        elite_count = min(5, max(1, self.population_size // 10))

        for generation in range(self.n_generations):
            fitness = self.score_population(score_fn)
            front = self.pareto_front(self.population)
            self.history[generation] = {
                "mean_composite": float(np.mean(fitness)),
                "max_composite": float(np.max(fitness)),
                "pareto_size": len(front),
            }
            selected = self.select(fitness)
            elites = [
                deepcopy(self.population[index]) for index in np.argsort(fitness)[-elite_count:]
            ]
            children: list[ProductIdea] = []
            cursor = 0
            while len(children) < self.population_size - elite_count:
                first = selected[cursor % len(selected)]
                second = selected[(cursor + 1) % len(selected)]
                children.append(self.mutate(self.crossover(first, second), attribute_pool))
                cursor += 2
            self.population = elites + children

        final_fitness = self.score_population(score_fn)
        front = self.pareto_front(self.population)
        fitness_by_id = {
            idea.id: score for idea, score in zip(self.population, final_fitness, strict=True)
        }
        return sorted(front, key=lambda idea: fitness_by_id[idea.id], reverse=True)
