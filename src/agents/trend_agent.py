"""
趋势洞察 Agent (TrendInsightAgent)
=================================
从社媒数据中提取消费趋势信号。
"""

from typing import Optional
from .base import BaseAgent


class TrendInsightAgent(BaseAgent):
    """趋势洞察 Agent: 分析社媒数据→提取趋势信号"""

    SYSTEM_PROMPT = """你是一个专业的消费趋势分析师，擅长从社交媒体数据中发现消费趋势。
请基于提供的数据，提取关键趋势信号并评分（0-1）。"""

    def __init__(self, llm_client=None):
        super().__init__("趋势洞察Agent", llm_client)

    def analyze_trends(self, social_data: list[dict]) -> list[dict]:
        """
        分析社媒数据提取趋势

        Returns:
            [{"trend": "国潮", "score": 0.85, "evidence": "..."}, ...]
        """
        prompt = f"""分析以下社媒趋势数据，提取 Top-5 消费趋势：
{str(social_data)[:2000]}

输出格式 (JSON):
[{{"trend": "趋势名", "score": 0.85, "evidence": "支撑依据"}}]
"""
        response = self.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=self.SYSTEM_PROMPT,
        )
        return self._parse_response(response)

    def _parse_response(self, response: str) -> list[dict]:
        """解析 LLM 输出为结构化数据"""
        import json
        try:
            start = response.index("[")
            end = response.rindex("]") + 1
            return json.loads(response[start:end])
        except (ValueError, json.JSONDecodeError):
            return [
                {"trend": "国潮IP联名", "score": 0.85, "evidence": "模拟: 社媒讨论度上升35%"},
                {"trend": "情绪价值产品", "score": 0.78, "evidence": "模拟: Z世代高关注"},
            ]
