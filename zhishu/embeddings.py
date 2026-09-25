"""文本嵌入（fastembed / BGE 系列，本地可跑，零 torch 依赖）。"""
from __future__ import annotations
from functools import lru_cache

from fastembed import TextEmbedding

from .config import get_settings


@lru_cache
def get_embedding_model() -> TextEmbedding:
    """懒加载并缓存嵌入模型。

    若配置了 embed_model_path（本地模型目录，含 model.onnx/tokenizer.json/config.json），
    则通过 specific_model_path 离线加载，跳过 HuggingFace 下载（适用于无外网/内网环境、
    或复用已下载模型）；否则首次调用会从 HuggingFace 下载权重。
    """
    s = get_settings()
    kwargs: dict = {}
    if s.embed_model_path:
        kwargs["specific_model_path"] = s.embed_model_path
    return TextEmbedding(model_name=s.embed_model, **kwargs)


@lru_cache
def embedding_dim() -> int:
    """返回当前嵌入模型的向量维度；embed_dim<=0 时自动探测。"""
    s = get_settings()
    if s.embed_dim and s.embed_dim > 0:
        return s.embed_dim
    model = get_embedding_model()
    dim = getattr(model, "dim", None)
    if dim:
        return int(dim)
    vec = next(iter(model.embed(["维度探测"])))
    return len(vec)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """批量将文本转为向量列表。"""
    if not texts:
        return []
    model = get_embedding_model()
    return [list(map(float, v)) for v in model.embed(texts)]
