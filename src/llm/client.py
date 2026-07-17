"""
本地 LLM 统一接口 (Ollama Client)
=============================
RTX 4090 本地推理，零 API Token 消耗。
支持: Qwen2.5-14B/32B, bge-m3 等所有 Ollama 模型。
"""

import logging
import os

import httpx

logger = logging.getLogger(__name__)


class LLMClient:
    """Ollama 本地大模型客户端 (兼容 OpenAI API 格式)"""

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: int = 120,
    ):
        self.model = model or os.getenv("MINISO_LLM_MODEL", "qwen2.5:14b")
        self.base_url = (
            base_url or os.getenv("MINISO_OLLAMA_URL", "http://localhost:11434")
        ).rstrip("/")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)
        self.last_call_mode = "not_called"

    def _ensure_ollama(self) -> bool:
        """检查 Ollama 服务是否运行"""
        try:
            r = self._client.get(f"{self.base_url}/api/tags")
            return r.status_code == 200
        except Exception:
            return False

    def chat(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """
        调用本地 LLM 进行对话。

        Args:
            messages: 对话历史 [{"role": "user", "content": "..."}, ...]
            system_prompt: 系统提示词
            temperature: 采样温度 (默认 self.temperature)
            max_tokens: 最大生成长度

        Returns:
            模型生成的文本
        """
        if not self._ensure_ollama():
            logger.warning("Ollama 未运行，使用模拟响应模式")
            self.last_call_mode = "mock"
            return self._mock_chat(messages)

        outbound_messages = list(messages)
        if system_prompt:
            outbound_messages = [{"role": "system", "content": system_prompt}, *outbound_messages]
        payload = {
            "model": self.model,
            "messages": outbound_messages,
            "stream": False,
            "options": {
                "temperature": self.temperature if temperature is None else temperature,
                "num_predict": self.max_tokens if max_tokens is None else max_tokens,
            },
        }

        try:
            r = self._client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
            self.last_call_mode = "ollama"
            return data.get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            self.last_call_mode = "mock"
            return self._mock_chat(messages)

    def _mock_chat(self, messages: list[dict]) -> str:
        """当 Ollama 不可用时的模拟响应（用于开发和测试）"""
        last_msg = messages[-1]["content"] if messages else ""
        return (
            f"[模拟响应] 针对「{last_msg[:50]}」的 AI 分析结果。"
            f"\n(注：实际运行时需启动 Ollama 并加载 {self.model})"
        )

    def generate_embedding(self, text: str, model: str = "bge-m3") -> list[float]:
        """生成文本嵌入向量"""
        if not self._ensure_ollama():
            return [0.0] * 768  # 模拟向量

        try:
            r = self._client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": model, "prompt": text},
            )
            r.raise_for_status()
            return r.json().get("embedding", [0.0] * 768)
        except Exception as e:
            logger.error(f"Embedding 调用失败: {e}")
            return [0.0] * 768

    def close(self):
        self._client.close()


class EmbeddingClient:
    """本地文本嵌入服务"""

    def __init__(self, model: str = "bge-m3", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self._client = httpx.Client(timeout=60)

    def encode(self, texts: str | list[str]) -> list[list[float]]:
        """编码文本为向量"""
        if isinstance(texts, str):
            texts = [texts]

        embeddings = []
        llm = LLMClient(base_url=self.base_url)
        try:
            for t in texts:
                emb = llm.generate_embedding(t, self.model)
                embeddings.append(emb)
        finally:
            llm.close()
        return embeddings

    def close(self):
        self._client.close()


if __name__ == "__main__":
    # 测试
    client = LLMClient()
    print(f"Ollama 可用: {client._ensure_ollama()}")
    resp = client.chat(messages=[{"role": "user", "content": "用一句话总结名创优品的商业模式。"}])
    print(f"响应: {resp}")
    client.close()
