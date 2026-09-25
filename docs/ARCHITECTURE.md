# 架构设计（Architecture）

## 1. 系统定位
智枢 ZhiShu：本地优先、混合推理的企业级 AI 系统 = **RAG 知识问答 + ReAct Agent 工具编排**，以 **REST API / CLI / React Web** 三种形态交付，Docker Compose 一键复现。

## 2. 分层架构
```
接入层  Web(React+TS) · CLI(Typer) · REST API(FastAPI)
   │
编排层  RAG Pipeline（检索→重排→生成）· Agent Core（ReAct）
   │
能力层  LLM Gateway · Retriever(向量+BM25) · Doc Ingest · Embeddings · Rerank
   │
存储/模型  Qdrant 向量库 · Ollama 本地 LLM · Cloud API(OpenAI 兼容)
   │
基础设施  Docker Compose · uv.lock 依赖锁定
```

## 3. 模块与接口（单一职责）
| 模块 | 职责 | 关键接口 | 错误码 |
|---|---|---|---|
| `ingest` | 多格式解析+分块+入库 | `ingest_file(path)` / `ingest_directory(dir)` / `ingest_texts(texts,metas)` | — |
| `embeddings` | 文本→向量 | `embed_texts(texts)→list[list[float]]`；`embedding_dim()` | — |
| `vector_store` | 向量库读写 | `upsert_texts` / `search(vec,top_k)` / `count` / `reset_collection` | E3xx |
| `rerank` | 候选重排（可插拔） | `Reranker.rerank(query,candidates,top_k)` | — |
| `retriever` | 两阶段检索 | `retrieve(query, top_k?, embed_fn?, search_fn?)` | E7xx |
| `llm` | 统一推理网关 | `LLMGateway.complete(messages)` / `.stream(messages)` | E5xx |
| `agent` | ReAct 编排 | `run_agent(query, llm?, tools?, max_steps?)` | E6xx |
| `rag` | 链路串联 | `answer(query, llm?, retriever_fn?)` / `answer_stream` | E7xx |
| `api` | REST 聚合 | `/api/ingest /search /rag /agent /chat /health /reset` | HTTP |
| `cli` | 命令行 | `ingest / ask / agent / search / health / eval / serve` | 进程码 |
| `eval` | 评测 | `run_eval(dataset, out, llm?)` | — |

## 4. 关键技术选型与依据
| 项 | 选型 | 理由 |
|---|---|---|
| 推理网关 | openai SDK（兼容 Ollama / DeepSeek 等） | 统一多后端、零额外重依赖、hybrid 自动降级 |
| 向量库 | Qdrant | Rust 实现、性能强、MIT、docker 一键 |
| 嵌入 | fastembed · `BAAI/bge-small-zh-v1.5` | 中文 SOTA 小模型、零 torch、~130MB |
| 重排 | HybridFusion（dense+BM25，可插拔） | 见下「偏离说明」 |
| Agent | 自研最小 ReAct | 见下「偏离说明」 |
| 后端 | FastAPI + Uvicorn | 异步、自动 OpenAPI 文档 |
| 前端 | React + TS + Vite | 契合技术栈、构建快 |
| 依赖锁定 | uv + uv.lock | 干净环境可复现 |

## 5. 与基线方案的偏离与书面说明
- **嵌入模型由 `BAAI/bge-m3` 改为 `BAAI/bge-small-zh-v1.5`**：fastembed 0.8.1 模型清单不含 `bge-m3`（仅含 bge-small/base 系列与 multilingual 版本）。`bge-small-zh-v1.5` 是清单内中文 SOTA 小模型，512 维、`embed_model` 可配置切换。
- **重排由「BGE Reranker」改为「HybridFusion（dense+BM25 融合）」**：fastembed 0.8.1 已移除 `TextReranker` 类；为避免引入 sentence-transformers+torch 这类体积大、版本敏感的依赖（违背「干净环境一键复现」），采用零额外依赖的融合重排。`Reranker` 为可插拔接口，后续可接入 BGE cross-encoder。
- **Agent 由 LangGraph 改为自研最小 ReAct**：LangGraph 依赖树重且版本波动大；自研实现接口清晰、可单测、可复现，符合「能复用不重写、确须自研须书面说明理由」。
- 上述均为可配置/可替换点，未偏离「复用领先开源成果」原则（Ollama、Qdrant、fastembed、FastAPI、React 均直接复用）。
