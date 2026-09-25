from zhishu.rerank import HybridFusionReranker


def test_rerank_orders_by_fusion():
    r = HybridFusionReranker()
    cands = [
        {"text": "退款 政策 7天 全额", "score": 0.90},
        {"text": "苹果 香蕉 水果 无关", "score": 0.95},
        {"text": "退款 政策 年假 计算", "score": 0.80},
    ]
    out = r.rerank("退款政策 7天", cands, top_k=2)
    assert out[0]["text"] == "退款 政策 7天 全额"
    assert len(out) == 2
    assert "fusion_score" in out[0]


def test_rerank_empty():
    assert HybridFusionReranker().rerank("q", []) == []


def test_rerank_no_topk_returns_all():
    r = HybridFusionReranker()
    cands = [{"text": "a 退款", "score": 0.5}, {"text": "b 无关", "score": 0.5}]
    out = r.rerank("退款", cands)
    assert len(out) == 2
