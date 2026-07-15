"""
评审 Agent (ReviewAgent)
========================
对产品创意进行多维度评审。
"""

from typing import Optional
from .base import BaseAgent


class ReviewAgent(BaseAgent):
    """评审 Agent: 评估创意爆品潜力和风险"""

    SYSTEM_PROMPT = """你是一个资深产品评审专家，从市场潜力、成本可行性、差异化三个维度评估产品创意。
输出评分（0-1）和具体建议。"""

    def review(self, idea: dict) -> dict:
        """
        评审单个产品创意

        Returns:
            {"market_potential": 0.85, "cost_feasibility": 0.7,
             "differentiation": 0.9, "overall": 0.82,
             "risk_factors": [...], "suggestions": [...]}
        """
        prompt = f"""评审以下产品创意：
品类: {idea.get('category', '未知')}
价格带: {idea.get('price_tier', '中价')}
风格: {idea.get('style', '简约')}
受众: {idea.get('target_audience', 'Z世代')}
特征: {idea.get('features', [])}

请从市场潜力、成本可行性、差异化三个维度评分，并给出具体建议。

输出 JSON:
{{"market_potential": 0.85, "cost_feasibility": 0.7, ...}}
"""
        response = self.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=self.SYSTEM_PROMPT,
        )
        return self._parse_response(response)

    def _parse_response(self, response: str) -> dict:
        import json
        try:
            start = response.index("{")
            end = response.rindex("}") + 1
            return json.loads(response[start:end])
        except (ValueError, json.JSONDecodeError):
            return {
                "market_potential": 0.78,
                "cost_feasibility": 0.65,
                "differentiation": 0.82,
                "overall": 0.75,
                "risk_factors": ["成本控制"],
                "suggestions": ["考虑简化包装降低成本"],
            }
