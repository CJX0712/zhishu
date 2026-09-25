"""文档入库：多格式解析（txt/md/json/html/pdf）→ 分块 → 写入向量库。"""
from __future__ import annotations
import json
import os
import re

from .vector_store import upsert_texts


def load_text(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(path)
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    if ext == ".json":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return "\n".join(str(d.get("text") or d.get("content") or "") for d in data)
        return str(data.get("text") or data.get("content") or json.dumps(data, ensure_ascii=False))
    if ext in (".html", ".htm"):
        with open(path, encoding="utf-8") as f:
            return re.sub(r"<[^>]+>", " ", f.read())
    with open(path, encoding="utf-8") as f:
        return f.read()


def chunk_text(text: str, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
    from .config import get_settings

    s = get_settings()
    size = chunk_size or s.chunk_size
    ov = overlap or s.chunk_overlap
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - ov
    return chunks


def ingest_texts(texts: list[str], metas: list[dict] | None = None, source: str = "inline") -> int:
    if metas is None:
        metas = [{"source": source, "chunk_index": i} for i in range(len(texts))]
    return upsert_texts(texts, metas)


def ingest_file(path: str, source: str | None = None) -> int:
    text = load_text(path)
    chunks = chunk_text(text)
    metas = [
        {"source": source or os.path.basename(path), "chunk_index": i}
        for i in range(len(chunks))
    ]
    return ingest_texts(chunks, metas)


def ingest_directory(dir_path: str, recursive: bool = True) -> int:
    exts = (".txt", ".md", ".json", ".html", ".htm", ".pdf")
    files: list[str] = []
    if recursive:
        for root, _, fs in os.walk(dir_path):
            for f in fs:
                if f.lower().endswith(exts):
                    files.append(os.path.join(root, f))
    else:
        for f in os.listdir(dir_path):
            if f.lower().endswith(exts):
                files.append(os.path.join(dir_path, f))
    total = 0
    for fp in files:
        total += ingest_file(fp)
    return total
