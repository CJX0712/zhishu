"""ZhiShu 全局配置（环境变量前缀 ZHISHU_，支持 .env）。"""
from __future__ import annotations
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ZHISHU_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- LLM 推理 ----
    llm_mode: str = "hybrid"            # local | cloud | hybrid
    llm_local_base_url: str = "http://localhost:11434/v1"
    llm_local_model: str = "qwen2.5:1.5b"
    llm_cloud_base_url: str = "https://api.deepseek.com/v1"
    llm_cloud_model: str = "deepseek-chat"
    llm_cloud_api_key: str = ""
    llm_temperature: float = 0.3
    llm_max_tokens: int = 1024
    llm_timeout: float = 60.0

    # ---- 嵌入 ----
    embed_model: str = "BAAI/bge-small-zh-v1.5"   # fastembed 已支持的中文 SOTA 小模型
    embed_model_path: str = ""                     # 本地模型目录（含 model.onnx/tokenizer.json/config.json）；非空则离线加载，跳过 HuggingFace 下载
    embed_dim: int = 0                             # 0 = 运行时自动探测

    # ---- 重排 ----
    rerank_enabled: bool = True
    rerank_type: str = "hybrid"                   # hybrid（dense+BM25 融合）| none
    rerank_top_k: int = 6

    # ---- 检索 ----
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    collection_name: str = "zhishu_docs"
    retrieval_top_k: int = 20
    final_top_k: int = 5
    chunk_size: int = 500
    chunk_overlap: int = 80

    # ---- 服务 / 杂项 ----
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "info"


@lru_cache
def get_settings() -> Settings:
    return Settings()
