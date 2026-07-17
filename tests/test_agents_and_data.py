from src.agents import AgentOrchestrator, CreativeGenerationAgent, ReviewAgent
from src.analysis import GrangerCausalAnalyzer, GrangerLeadAnalyzer, SocialSalesCorrelation
from src.pipeline.data_generator import (
    generate_miniso_sample_data,
    generate_social_trend_data,
)


class FakeLLM:
    last_call_mode = "test"

    def chat(self, messages, system_prompt=None):
        del system_prompt
        text = messages[-1]["content"]
        if "Top-5" in text:
            return '[{"trend":"国潮","score":0.8,"evidence":"test"}]'
        if "生成" in text:
            return '[{"category":"家居","price_tier":"中价","style":"国潮","target_audience":"学生","material":"陶瓷","features":["便携"]}]'
        return '{"market_potential":0.8,"cost_feasibility":0.7,"differentiation":0.6,"overall":0.7}'

    def close(self):
        pass


def test_agents_share_injected_client_and_rank_reviews():
    fake = FakeLLM()
    assert CreativeGenerationAgent(fake).llm is fake
    assert ReviewAgent(fake).llm is fake
    result = AgentOrchestrator(fake).run_pipeline([{"text": "trend data"}])
    assert result["summary"]["n_ideas"] == 1
    assert result["summary"]["llm_mode"] == "test"


def test_synthetic_product_rows_are_unique_and_auditable():
    frame = generate_miniso_sample_data(n_products=300, n_days=400, seed=3)
    assert frame["product_id"].is_unique
    assert set(["social_score", "is_hit", "sales_90d", "data_provenance"]) <= set(frame)
    assert frame["data_provenance"].eq("synthetic-demo-v2").all()


def test_lag_correlation_finds_the_leading_signal():
    frame = generate_social_trend_data(n_days=400, seed=5)
    correlations = SocialSalesCorrelation().lag_correlation(
        frame["social_momentum"], frame["sales"], max_lag=7
    )
    assert max(correlations, key=correlations.get) == 3


def test_granger_api_states_predictive_not_structural_causality():
    frame = generate_social_trend_data(n_days=160, seed=5)
    result = GrangerLeadAnalyzer(max_lag=3).test_predictive_lead(
        frame["social_momentum"], frame["sales"]
    )

    assert result["is_predictive_lead"] is True
    assert result["interpretation"] == "predictive_lead_not_structural_causality"
    assert result["is_causal"] == result["is_predictive_lead"]
    assert GrangerCausalAnalyzer is GrangerLeadAnalyzer
