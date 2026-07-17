"""
Agent 编排器 (Agent Orchestrator)
================================
管理多 Agent 协作流程。
"""

import time
import uuid

from .creative_agent import CreativeGenerationAgent
from .review_agent import ReviewAgent
from .trend_agent import TrendInsightAgent


class AgentOrchestrator:
    """
    Agent 编排器：串联趋势洞察 → 创意生成 → 评审
    """

    def __init__(self, llm_client=None):
        self.trend_agent = TrendInsightAgent(llm_client)
        self.creative_agent = CreativeGenerationAgent(llm_client)
        self.review_agent = ReviewAgent(llm_client)

    def run_pipeline(self, social_data: list[dict]) -> dict:
        """
        执行完整 Agent 管线

        Returns:
            {"trends": [...], "ideas": [...], "reviews": [...], "summary": {...}}
        """
        trace_id = uuid.uuid4().hex[:12]
        started_at = time.perf_counter()
        print(f"[Orchestrator] 启动 Agent 管线 trace_id={trace_id}")

        # Step 1: 趋势洞察
        print("[Orchestrator] 📊 趋势洞察中...")
        trends = self.trend_agent.analyze_trends(social_data)

        # Step 2: 创意生成
        print("[Orchestrator] 💡 创意生成中...")
        ideas = self.creative_agent.generate_ideas(trends)

        # Step 3: 评审
        print("[Orchestrator] ⭐ 评审中...")
        reviews = []
        for idea in ideas:
            review = self.review_agent.review(idea)
            reviews.append({"idea": idea, "review": review})

        # 汇总
        avg_score = (
            sum(r["review"].get("overall", 0) for r in reviews) / len(reviews) if reviews else 0
        )

        ranked_reviews = sorted(
            reviews,
            key=lambda item: float(item["review"].get("overall", 0)),
            reverse=True,
        )
        summary = {
            "trace_id": trace_id,
            "n_trends": len(trends),
            "n_ideas": len(ideas),
            "avg_review_score": avg_score,
            "top_idea": ranked_reviews[0] if ranked_reviews else None,
            "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
            "llm_mode": getattr(self.trend_agent.llm, "last_call_mode", "unknown"),
        }

        return {
            "trends": trends,
            "ideas": ideas,
            "reviews": reviews,
            "summary": summary,
        }
