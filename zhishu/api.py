"""REST API（FastAPI）：/api/ingest /search /rag /agent /chat /health /reset。"""
from __future__ import annotations
import os
from typing import Optional

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import agent as agent_mod, ingest, rag, retriever
from .llm import LLMError
from .vector_store import count, reset_collection

app = FastAPI(title="ZhiShu API", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

router = APIRouter()


class IngestRequest(BaseModel):
    text: Optional[str] = None
    file_path: Optional[str] = None
    source: Optional[str] = None


class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = None
    stream: bool = False


class ChatRequest(BaseModel):
    messages: list[dict]
    model: Optional[str] = None


class AgentRequest(BaseModel):
    query: str


@router.get("/health")
def health():
    return {"status": "ok", "docs": count()}


@router.post("/ingest")
def ingest_endpoint(req: IngestRequest):
    try:
        if req.file_path:
            n = ingest.ingest_file(req.file_path, source=req.source)
        elif req.text:
            n = ingest.ingest_texts([req.text], source=req.source or "inline")
        else:
            raise HTTPException(400, "需提供 text 或 file_path")
        return {"ingested": n}
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"入库失败: {e}")


@router.post("/search")
def search_endpoint(req: QueryRequest):
    try:
        return {"results": retriever.retrieve(req.query, top_k=req.top_k)}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"检索失败: {e}")


@router.post("/rag")
def rag_endpoint(req: QueryRequest):
    try:
        if req.stream:
            out = rag.answer_stream(req.query)
            return StreamingResponse(out["stream"], media_type="text/plain")
        return rag.answer(req.query)
    except LLMError as e:
        raise HTTPException(502, str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"RAG 失败: {e}")


@router.post("/agent")
def agent_endpoint(req: AgentRequest):
    try:
        return agent_mod.run_agent(req.query)
    except LLMError as e:
        raise HTTPException(502, str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"Agent 失败: {e}")


@router.post("/chat")
def chat_endpoint(req: ChatRequest):
    from .llm import OpenAIGateway

    try:
        gw = OpenAIGateway()
        return {"answer": gw.complete(req.messages, model=req.model)}
    except LLMError as e:
        raise HTTPException(502, str(e))


@router.post("/reset")
def reset_endpoint():
    reset_collection()
    return {"reset": True}


app.include_router(router, prefix="/api")

# 若前端已构建，挂载静态资源（放在最后，API 路由优先匹配）
_DIST = os.path.join(os.path.dirname(__file__), "..", "web", "dist")
if os.path.isdir(_DIST):
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="ui")
