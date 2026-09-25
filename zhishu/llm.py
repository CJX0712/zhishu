"""LLM 推理网关：统一本地(Ollama)/云端(OpenAI 兼容)接口，支持 hybrid 自动降级。

设计说明：复用 openai python SDK（同时兼容 Ollama 的 OpenAI 兼容端点与 DeepSeek/OpenAI 等云端），
避免在依赖树中引入 litellm 这类体积大、版本敏感的组件，保证干净环境一键复现。
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterable, Iterator, Optional

from openai import OpenAI

from .config import get_settings


class LLMError(Exception):
    """LLM 调用统一异常（对应错误码 E5xx）。"""


class LLM(ABC):
    """可被注入的 LLM 接口：rag / agent 仅依赖此抽象。"""

    @abstractmethod
    def complete(self, messages: list[dict], model: Optional[str] = None) -> str: ...

    @abstractmethod
    def stream(self, messages: list[dict], model: Optional[str] = None) -> Iterator[str]: ...


class OpenAIGateway(LLM):
    def __init__(self, settings=None):
        self.s = settings or get_settings()
        self._local: Optional[OpenAI] = None
        self._cloud: Optional[OpenAI] = None

    # ---- 客户端（惰性创建）----
    def _local_client(self) -> OpenAI:
        if self._local is None:
            self._local = OpenAI(
                base_url=self.s.llm_local_base_url,
                api_key="ollama",
                timeout=self.s.llm_timeout,
            )
        return self._local

    def _cloud_client(self) -> OpenAI:
        if self._cloud is None:
            self._cloud = OpenAI(
                base_url=self.s.llm_cloud_base_url,
                api_key=self.s.llm_cloud_api_key or "EMPTY",
                timeout=self.s.llm_timeout,
            )
        return self._cloud

    def _create(self, client: OpenAI, model: str, messages: list[dict], stream: bool):
        return client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=self.s.llm_temperature,
            max_tokens=self.s.llm_max_tokens,
            stream=stream,
        )

    # ---- 非流式 ----
    def complete(self, messages: list[dict], model: Optional[str] = None) -> str:
        s = self.s
        mode = s.llm_mode
        last_err = None
        if mode in ("local", "hybrid"):
            try:
                resp = self._create(
                    self._local_client(), model or s.llm_local_model, messages, False
                )
                return resp.choices[0].message.content or ""
            except Exception as e:  # noqa: BLE001
                last_err = e
                if mode == "local":
                    raise LLMError(f"本地 LLM 调用失败: {e}") from e
        if mode in ("cloud", "hybrid"):
            if not s.llm_cloud_api_key:
                if mode == "cloud":
                    raise LLMError("未配置云端 API Key (ZHISHU_LLM_CLOUD_API_KEY)")
                raise LLMError(f"本地推理失败且无云端 Key 兜底: {last_err}")
            try:
                resp = self._create(
                    self._cloud_client(), model or s.llm_cloud_model, messages, False
                )
                return resp.choices[0].message.content or ""
            except Exception as e:  # noqa: BLE001
                raise LLMError(f"云端 LLM 调用失败: {e}") from e
        raise LLMError(f"未知推理模式: {mode}")

    # ---- 流式 ----
    def stream(self, messages: list[dict], model: Optional[str] = None) -> Iterator[str]:
        s = self.s
        mode = s.llm_mode
        last_err = None
        if mode in ("local", "hybrid"):
            try:
                resp = self._create(
                    self._local_client(), model or s.llm_local_model, messages, True
                )
                return self._iter(resp)
            except Exception as e:  # noqa: BLE001
                last_err = e
                if mode == "local":
                    raise LLMError(f"本地 LLM 流式失败: {e}") from e
        if mode in ("cloud", "hybrid"):
            if not s.llm_cloud_api_key:
                raise LLMError(f"本地推理失败且无云端 Key 兜底: {last_err}")
            try:
                resp = self._create(
                    self._cloud_client(), model or s.llm_cloud_model, messages, True
                )
                return self._iter(resp)
            except Exception as e:  # noqa: BLE001
                raise LLMError(f"云端 LLM 流式失败: {e}") from e
        raise LLMError(f"未知推理模式: {mode}")

    @staticmethod
    def _iter(resp) -> Iterator[str]:
        for chunk in resp:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
