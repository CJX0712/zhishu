"""重排层（可插拔）。

默认实现 HybridFusionReranker：对检索返回的候选做「稠密相似度 + BM25 词法」融合重排，
无需额外模型、零外部依赖，对中文做字/词混合切分。
接口 Reranker.rerank(query, candidates, top_k) 可被 BGE cross-encoder 等实现替换。
"""
from __future__ import annotations
import re
from typing import Optional

from rank_bm25 import BM25Okapi


def tokenize(text: str) -> list[str]:
    """中文按「字 + 二元字」切分，英文按空白切分，获得可用词法信号。"""
    if re.search(r"[㐀-鿿]", text):
        chars = list(re.sub(r"\s+", "", text))
        return chars + [a + b for a, b in zip(chars, chars[1:])]
    return text.split()


class Reranker:
    def rerank(self, query: str, candidates: list[dict], top_k: Optional[int] = None):
        raise NotImplementedError


class HybridFusionReranker(Reranker):
    def rerank(
        self, query: str, candidates: list[dict], top_k: Optional[int] = None
    ) -> list[dict]:
        if not candidates:
            return []
        docs = [c["text"] for c in candidates]
        bm25 = BM25Okapi([tokenize(d) for d in docs])
        bm25_scores = bm25.get_scores(tokenize(query))

        dense = [float(c.get("score", 0.0)) for c in candidates]
        dmin, dmax = min(dense), max(dense)
        dnorm = [
            (d - dmin) / (dmax - dmin) if dmax > dmin else 1.0 for d in dense
        ]
        bmin, bmax = float(min(bm25_scores)), float(max(bm25_scores))
        bnorm = [
            (b - bmin) / (bmax - bmin) if bmax > bmin else 0.0 for b in bm25_scores
        ]
        fused = [0.7 * d + 0.3 * b for d, b in zip(dnorm, bnorm)]
        order = sorted(range(len(candidates)), key=lambda i: fused[i], reverse=True)
        out = [
            dict(candidates[i], fusion_score=round(fused[i], 4)) for i in order
        ]
        return out[:top_k] if top_k else out


def get_reranker() -> Optional[Reranker]:
    from .config import get_settings

    s = get_settings()
    if not s.rerank_enabled or s.rerank_type == "none":
        return None
    # 预留扩展点：若未来接入 BGE cross-encoder，可在此实例化并返回。
    return HybridFusionReranker()
