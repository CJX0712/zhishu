"""检索编排：向量检索 →（可选）重排 → 返回最终上下文。"""
from __future__ import annotations
from typing import Callable, Optional

from .config import get_settings
from .embeddings import embed_texts
from .rerank import get_reranker
from .vector_store import search


def retrieve(
    query: str,
    top_k: Optional[int] = None,
    embed_fn: Optional[Callable[[list[str]], list[list[float]]]] = None,
    search_fn: Optional[Callable] = None,
) -> list[dict]:
    """两阶段检索：dense 向量召回 → hybrid 融合重排。

    embed_fn / search_fn 可注入，便于单测用假实现。
    """
    s = get_settings()
    embed_fn = embed_fn or embed_texts
    search_fn = search_fn or search

    qv = embed_fn([query])[0]
    candidates = search_fn(qv, top_k=s.retrieval_top_k)

    reranker = get_reranker()
    if reranker:
        candidates = reranker.rerank(query, candidates, top_k=s.final_top_k)
    else:
        candidates = candidates[: s.final_top_k]
    return candidates
