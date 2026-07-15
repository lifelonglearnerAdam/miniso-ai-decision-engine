"""
Agent 基类
"""

from abc import ABC, abstractmethod
from typing import Optional
from src.llm.client import LLMClient


class BaseAgent(ABC):
    """所有 Agent 的抽象基类"""

    def __init__(self, name: str, llm_client: Optional[LLMClient] = None):
        self.name = name
        self.llm = llm_client or LLMClient()

    @abstractmethod
    def run(self, *args, **kwargs):
        """执行 Agent 主逻辑"""
        pass

    def chat(self, messages: list[dict], system_prompt: Optional[str] = None) -> str:
        """统一的 LLM 调用接口"""
        return self.llm.chat(messages, system_prompt=system_prompt)
