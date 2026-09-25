import hashlib

from zhishu.retriever import retrieve


def _fake_embed(texts):
    out = []
    for t in texts:
        v = [
            int.from_bytes(hashlib.md5(f"{t}|{i}".encode()).digest()[:4], "big")
            / 2**32
            * 2
            - 1
            for i in range(8)
        ]
        out.append(v)
    return out


def test_retriever_full_pipeline():
    def search_fn(qv, top_k=10):
        return [
            {"id": 1, "score": 0.90, "text": "退款政策七天全额退款", "meta": {}},
            {"id": 2, "score": 0.80, "text": "苹果香蕉水果营养", "meta": {}},
        ]

    res = retrieve("退款政策", embed_fn=_fake_embed, search_fn=search_fn)
    assert len(res) == 2
    assert res[0]["text"] == "退款政策七天全额退款"


def test_retriever_empty():
    res = retrieve(
        "x",
        embed_fn=_fake_embed,
        search_fn=lambda qv, top_k=10: [],
    )
    assert res == []
