"""
Agent 基类
"""

from src.llm.client import LLMClient


class BaseAgent:
    """所有 Agent 的抽象基类"""

    def __init__(self, name: str, llm_client: LLMClient | None = None):
        self.name = name
        self.llm = llm_client or LLMClient()

    def run(self, *args, **kwargs):
        """Execute the agent's primary operation."""
        raise NotImplementedError

    def chat(self, messages: list[dict], system_prompt: str | None = None) -> str:
        """统一的 LLM 调用接口"""
        return self.llm.chat(messages, system_prompt=system_prompt)

    def close(self) -> None:
        """Release the shared HTTP client when the agent owns the lifecycle."""
        self.llm.close()
