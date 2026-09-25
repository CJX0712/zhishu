"""测试公共夹具：确定性嵌入（免下载大模型）、测试集合隔离、Qdrant 可用性跳过。"""
import hashlib

import numpy as np
import pytest

import zhishu.embeddings as emb
import zhishu.vector_store as vs
from zhishu.config import get_settings


class DeterministicEmbed:
    """测试用确定性嵌入，维度固定，避免下载 BGE 权重。"""

    def __init__(self, dim: int = 64):
        self.dim = dim

    def embed(self, texts):
        for t in texts:
            v = [
                int.from_bytes(hashlib.md5(f"{t}|{i}".encode()).digest()[:4], "big")
                / 2**32
                * 2
                - 1
                for i in range(self.dim)
            ]
            yield np.array(v, dtype="float32")


@pytest.fixture(autouse=True)
def _setup(monkeypatch):
    monkeypatch.setenv("ZHISHU_COLLECTION_NAME", "zhishu_test")
    monkeypatch.setattr(emb, "get_embedding_model", lambda: DeterministicEmbed(64))
    emb.embedding_dim.cache_clear()
    get_settings.cache_clear()
    try:
        vs.reset_collection()
    except Exception:
        pass
    yield
    try:
        vs.reset_collection()
    except Exception:
        pass


@pytest.fixture
def requires_qdrant():
    try:
        vs.get_client().get_collections()
    except Exception:
        pytest.skip("Qdrant 不可用，跳过需要向量库的测试")
