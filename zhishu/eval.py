"""评测工具：基于检索上下文的量化指标（context_recall / faithfulness / answer_relevancy / 延迟）。

内置指标零额外依赖；若已安装 ragas，可在 run_eval(use_ragas=True) 时调用其指标做交叉验证。
"""
from __future__ import annotations
import json
import os
import re
import time
from typing import Optional

from . import rag
from .llm import LLM, LLMError


def _tok(text: str) -> set[str]:
    text = (text or "").lower()
    # 拉丁/数字按词切分；CJK 逐字切分（避免整句被当成单一 token 导致中文重叠恒为 0）
    toks = re.findall(r"[\w]+", text)
    cjk = re.findall(r"[㐀-鿿]", text)
    return set(toks) | set(cjk)


def context_recall(reference: str, contexts: list[dict]) -> float:
    if not reference:
        return 0.0
    ref = _tok(reference)
    if not ref:
        return 0.0
    ctx: set[str] = set()
    for c in contexts:
        ctx |= _tok(c.get("text", ""))
    return len(ref & ctx) / len(ref)


def faithfulness(answer: str, contexts: list[dict]) -> float:
    """简易蕴含：答案句子与上下文词重叠≥30% 视为有依据。"""
    if not answer:
        return 1.0
    ctx: set[str] = set()
    for c in contexts:
        ctx |= _tok(c.get("text", ""))
    sents = [s for s in re.split(r"[。.!?！？\n]", answer) if s.strip()]
    if not sents:
        return 1.0
    supported = 0
    for s in sents:
        st = _tok(s)
        if not st or len(st) <= 3:
            supported += 1
            continue
        if len(st & ctx) / len(st) >= 0.3:
            supported += 1
    return supported / len(sents)


def answer_relevancy(question: str, answer: str) -> float:
    if not answer:
        return 0.0
    q, a = _tok(question), _tok(answer)
    if not q or not a:
        return 0.0
    return len(q & a) / len(q)


def run_eval(
    dataset_path: str = "data/eval/sample.json",
    out_path: Optional[str] = "data/eval/report.json",
    llm: Optional[LLM] = None,
    use_ragas: bool = False,
) -> dict:
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(dataset_path)
    with open(dataset_path, encoding="utf-8") as f:
        items = json.load(f)

    ragas_metrics: Optional[dict] = None
    if use_ragas:
        ragas_metrics = _ragas_metrics(items, llm)

    rows = []
    latencies = []
    for it in items:
        q = it["question"]
        ref = it.get("reference_answer", "")
        t0 = time.time()
        try:
            res = rag.answer(q, llm=llm)
        except LLMError as e:
            res = {"answer": f"[LLM错误] {e}", "citations": [], "contexts": []}
        dt = time.time() - t0
        latencies.append(dt)
        rows.append(
            {
                "question": q,
                "answer": res["answer"],
                "context_recall": round(context_recall(ref, res.get("contexts", [])), 3),
                "faithfulness": round(faithfulness(res["answer"], res.get("contexts", [])), 3),
                "answer_relevancy": round(answer_relevancy(q, res["answer"]), 3),
                "latency_s": round(dt, 3),
                "citations": len(res["citations"]),
            }
        )

    n = len(rows) or 1
    summary = {
        "samples": len(rows),
        "context_recall_avg": round(sum(r["context_recall"] for r in rows) / n, 3),
        "faithfulness_avg": round(sum(r["faithfulness"] for r in rows) / n, 3),
        "answer_relevancy_avg": round(sum(r["answer_relevancy"] for r in rows) / n, 3),
        "avg_latency_s": round(sum(latencies) / n, 3),
    }
    if ragas_metrics:
        summary["ragas"] = ragas_metrics
    report = {"summary": summary, "details": rows}
    if out_path:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    return report


def _ragas_metrics(items: list[dict], llm: Optional[LLM]) -> dict:
    try:
        from ragas import evaluate
        from ragas.metrics import (
            faithfulness as r_faith,
            answer_relevancy as r_rel,
            context_recall as r_cr,
        )
        from datasets import Dataset
    except Exception as e:  # noqa: BLE001
        return {"error": f"ragas 不可用: {e}"}
    # ragas 需要 LLM；若未注入则跳过
    if llm is None:
        return {"error": "ragas 需要注入 LLM"}
    data = {
        "question": [i["question"] for i in items],
        "answer": [rag.answer(i["question"], llm=llm)["answer"] for i in items],
        "contexts": [[c["text"] for c in rag.answer(i["question"], llm=llm).get("contexts", [])] for i in items],
    }
    ds = Dataset.from_dict(data)
    score = evaluate(ds, metrics=[r_faith, r_rel, r_cr])
    return dict(score)
