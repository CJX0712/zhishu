"""向量存储（Qdrant）：集合管理、写入、向量检索、计数、重置。"""
from __future__ import annotations
import hashlib
from functools import lru_cache
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
)

from .config import get_settings
from .embeddings import embedding_dim, embed_texts


def _stable_id(seed: str) -> int:
    return int(hashlib.md5(seed.encode("utf-8")).hexdigest()[:16], 16)


@lru_cache
def get_client() -> QdrantClient:
    s = get_settings()
    return QdrantClient(host=s.qdrant_host, port=s.qdrant_port, timeout=10)


def ensure_collection(client: Optional[QdrantClient] = None) -> QdrantClient:
    s = get_settings()
    client = client or get_client()
    if not client.collection_exists(s.collection_name):
        client.create_collection(
            s.collection_name,
            vectors_config=VectorParams(
                size=embedding_dim(), distance=Distance.COSINE
            ),
        )
    return client


def upsert_texts(
    texts: list[str],
    metas: list[dict],
    vectors: Optional[list[list[float]]] = None,
    client: Optional[QdrantClient] = None,
) -> int:
    """写入文本块（自动嵌入），返回写入条数。id 由内容稳定哈希，重复写入幂等。"""
    s = get_settings()
    client = client or get_client()
    ensure_collection(client)
    if vectors is None:
        vectors = embed_texts(texts)
    points = [
        PointStruct(
            id=_stable_id(f"{m.get('source','')}|{m.get('chunk_index',i)}|{t}"),
            vector=v,
            payload={"text": t, "meta": m},
        )
        for i, (t, m, v) in enumerate(zip(texts, metas, vectors))
    ]
    client.upsert(s.collection_name, points=points)
    return len(points)


def search(
    query_vector: list[float],
    top_k: Optional[int] = None,
    client: Optional[QdrantClient] = None,
) -> list[dict]:
    """向量检索，返回候选 [{id,score,text,meta}]。"""
    s = get_settings()
    client = client or get_client()
    top_k = top_k or s.retrieval_top_k
    ensure_collection(client)
    resp = client.query_points(
        s.collection_name, query=query_vector, limit=top_k, with_payload=True
    )
    hits = resp.points
    return [
        {
            "id": h.id,
            "score": float(h.score),
            "text": (h.payload or {}).get("text", ""),
            "meta": (h.payload or {}).get("meta", {}),
        }
        for h in hits
    ]


def count(client: Optional[QdrantClient] = None) -> int:
    s = get_settings()
    client = client or get_client()
    if not client.collection_exists(s.collection_name):
        return 0
    return client.count(s.collection_name).count


def reset_collection(client: Optional[QdrantClient] = None) -> None:
    s = get_settings()
    client = client or get_client()
    if client.collection_exists(s.collection_name):
        client.delete_collection(s.collection_name)
