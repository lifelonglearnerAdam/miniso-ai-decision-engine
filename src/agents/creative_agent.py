"""
创意生成 Agent (CreativeGenerationAgent)
======================================
基于趋势生成产品创意。
"""

from typing import Optional
from .base import BaseAgent


class CreativeGenerationAgent(BaseAgent):
    """创意生成 Agent: 趋势→产品创意"""

    SYSTEM_PROMPT = """你是一个创意产品设计师，擅长将消费趋势转化为具体可落地的产品创意。
请输出结构化的产品概念。"""

    def generate_ideas(self, trends: list[dict], n_ideas: int = 5) -> list[dict]:
        """
        基于趋势生成产品创意

        Args:
            trends: 趋势列表 [{"trend": "...", "score": ...}]
            n_ideas: 生成创意数量

        Returns:
            [{"category": "...", "price_tier": "...", "style": "...", ...}]
        """
        prompt = f"""基于以下消费趋势，生成 {n_ideas} 个名创优品可落地的产品创意：

趋势: {str(trends)[:1000]}

每个创意需包含: category, price_tier, style, target_audience, material, features

输出 JSON 格式。
"""
        response = self.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=self.SYSTEM_PROMPT,
        )
        return self._parse_response(response)

    def _parse_response(self, response: str) -> list[dict]:
        import json
        try:
            start = response.index("[")
            end = response.rindex("]") + 1
            return json.loads(response[start:end])
        except (ValueError, json.JSONDecodeError):
            return [
                {"category": "家居", "price_tier": "中价", "style": "国潮",
                 "target_audience": "Z世代", "material": "陶瓷",
                 "features": ["故宫联名", "茶具套装", "礼盒包装"]},
            ]
