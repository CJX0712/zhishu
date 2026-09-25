"""RAG 链路：检索上下文 → 组装提示 → LLM 生成（带引用溯源）。"""
from __future__ import annotations
from typing import Callable, Iterator, Optional

from .llm import LLM, OpenAIGateway
from .retriever import retrieve

RAG_SYSTEM = (
    "你是一个严谨的企业知识助手。仅依据【参考资料】回答问题；"
    "若资料中无相关信息，明确回答“资料中未提及”，不得编造。"
    "回答时请在相关句末用 [1]、[2] 标注引用，序号对应参考资料编号。"
)


def build_messages(query: str, contexts: list[dict]) -> list[dict]:
    ctx_block = "\n\n".join(f"[{i + 1}] {c['text']}" for i, c in enumerate(contexts))
    user = f"【参考资料】\n{ctx_block}\n\n【问题】{query}"
    return [
        {"role": "system", "content": RAG_SYSTEM},
        {"role": "user", "content": user},
    ]


def _default_llm() -> LLM:
    return OpenAIGateway()


def answer(
    query: str,
    llm: Optional[LLM] = None,
    retriever_fn: Optional[Callable[[str], list[dict]]] = None,
) -> dict:
    llm = llm or _default_llm()
    contexts = (retriever_fn or retrieve)(query)
    if not contexts:
        return {"answer": "资料库为空或未检索到相关内容。", "citations": [], "contexts": []}
    messages = build_messages(query, contexts)
    text = llm.complete(messages)
    citations = [
        {
            "index": i + 1,
            "source": c.get("meta", {}).get("source", ""),
            "text": c["text"],
        }
        for i, c in enumerate(contexts)
    ]
    return {"answer": text, "citations": citations, "contexts": contexts}


def answer_stream(
    query: str,
    llm: Optional[LLM] = None,
    retriever_fn: Optional[Callable[[str], list[dict]]] = None,
):
    llm = llm or _default_llm()
    contexts = (retriever_fn or retrieve)(query)
    messages = build_messages(query, contexts)

    def gen() -> Iterator[str]:
        for tok in llm.stream(messages):
            yield tok

    return {"contexts": contexts, "stream": gen()}
