from src.evolution import DFMConstraintEngine, EvolutionEngine, ProductIdea

POOL = {
    "categories": ["家居", "食品", "数码配件", "玩具"],
    "price_tiers": ["低价", "中价", "高价"],
    "styles": ["简约", "国潮", "IP联名"],
    "audiences": ["学生", "白领", "亲子"],
    "materials": ["塑料", "陶瓷", "金属"],
    "features": ["便携", "环保", "多功能", "防水", "OLED"],
}


def test_population_size_and_true_pareto_front():
    engine = EvolutionEngine(population_size=20, n_generations=4, random_state=4)
    front = engine.run([{"category": "家居", "features": ["便携"], "material": "陶瓷"}], POOL)
    assert len(engine.population) == 20
    assert front
    for candidate in front:
        assert not any(
            other.id != candidate.id
            and all(a >= b for a, b in zip(other.objectives, candidate.objectives, strict=True))
            and any(a > b for a, b in zip(other.objectives, candidate.objectives, strict=True))
            for other in engine.population
        )


def test_dfm_rules_are_explicit_not_keyword_substrings():
    idea = ProductIdea(
        id="risk",
        category="数码配件",
        price_tier="低价",
        style="简约",
        target_audience="学生",
        material="塑料",
        features=["OLED", "防水"],
    )
    score, reasons = DFMConstraintEngine().evaluate_with_reasons(idea)
    assert score < 1
    assert {reason.rule_id for reason in reasons} == {
        "low_price_oled",
        "electronics_waterproof",
    }
