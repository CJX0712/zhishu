from zhishu import ingest, rag


class MockLLM:
    def complete(self, messages, model=None):
        return "根据资料，发货后7天内可全额退款。[1]"

    def stream(self, messages, model=None):
        yield "根据资料"


def test_rag_end_to_end(requires_qdrant):
    ingest.ingest_texts(
        ["退款政策：发货后7天内可全额退款。"],
        [{"source": "t", "chunk_index": 0}],
    )
    res = rag.answer("几天内可以全额退款？", llm=MockLLM())
    assert res["answer"]
    assert res["citations"]
    assert len(res["contexts"]) >= 1


def test_rag_empty_kb():
    res = rag.answer("空库问题", llm=MockLLM())
    assert "资料库为空" in res["answer"]
    assert res["citations"] == []
