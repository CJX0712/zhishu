# 智枢 ZhiShu · AI 知识中枢与智能体平台 — 系统方案（开工基线 v0.1）

> 作者：晨星 ｜ 日期：2026-09-25 ｜ 状态：待确认开工

## 0. 结论（Conclusion First）
交付一套**本地优先、混合推理**的企业级 AI 系统：**RAG 知识问答 + Agent 工具编排**，统一以 **FastAPI REST / CLI / React Web** 三种形态交付，全部由 **Docker Compose 一键拉起**，依赖版本锁定、测试覆盖、性能基线可量化对标 SOTA。

核心决策：
- 推理：本地 Ollama 跑 4-bit 量化 Qwen2.5（离线可跑）；云端 OpenAI 兼容 API（DeepSeek 等）作兜底；统一经 **LiteLLM 网关**切换。
- 检索：Qdrant 向量库 + BGE-M3 嵌入 + BGE Reranker 重排（混合稀疏/稠密检索）。
- 编排：LangGraph 实现 ReAct Agent（工具可插拔）；若依赖冲突不可解则自研轻量编排并书面说明。
- 评测：RAGAS + 自建中文 benchmark，输出量化基线并与 naive baseline / 公开 SOTA 对比。

## 1. 能力边界
**范围内：**
- 多格式文档入库（PDF/Markdown/HTML/TXT/Office）→ 解析→分块→嵌入→入库
- 混合检索（向量 + 关键词 BM25）→ 重排 → 带引用溯源的生成
- Agent：基于工具调用的多步推理（搜索/计算/查库/代码执行沙箱）
- 混合推理：本地/云端统一接口，自动降级
- 三形态交付：Web / REST API / CLI
- 评测与性能基线

**范围外（非目标）：**
- 不训练、不微调模型（仅推理复用）
- 不做图像/视频/音频多模态生成
- 不做分布式训练集群
- 不做多租户权限隔离（预留接口，本期不实现）

## 2. 技术栈与选型依据
| 模块 | 选型 | 备选 | 选型理由（性能/生态/许可证/活跃度） |
|---|---|---|---|
| LLM 网关 | LiteLLM + Ollama(local) / OpenAI-compatible(cloud) | 自研路由 | 统一多后端、active 维护、MIT；避免重复造轮子 |
| 向量库 | Qdrant | Milvus/Chroma/Weaviate | 性能强、Rust 实现、MIT、docker 一键、过滤语法强 |
| Embedding | BGE-M3 (fastembed) | bge-large-zh | MTEB 多语 SOTA、支持稠密/稀疏/多语、Apache-2.0 |
| Reranker | BGE Reranker-large | Cohere/自研 | 中文重排 SOTA、开源可本地部署 |
| 编排 | LangGraph | 自研 ReAct | 工业标准、可状态化、MIT；冲突则自研并说明 |
| 后端 | FastAPI + Uvicorn | Flask | 异步、OpenAPI 自动文档、生态成熟 |
| 前端 | React + TS + Vite | Vue | 契合用户技术栈、构建快 |
| CLI | Typer | argparse | 类型安全、易用 |
| 评测 | RAGAS + pytest | 自研 | RAG 评测事实标准、可量化 |
| 依赖锁定 | uv/poetry + lockfile + Docker pin | pip freeze | 干净环境可复现 |
| 容器 | Docker Compose | k8s | 单机一键、零编排复杂度 |

## 3. 模块划分与接口清单
| 模块 | 职责 | 输入 | 输出 | 协议 | 错误码 |
|---|---|---|---|---|---|
| doc-ingest | 文档解析/清洗/分块 | file_path / raw text, chunk_size | List[Chunk{id,text,meta}] | 内部函数 / API POST /ingest | E100 解析失败, E101 不支持格式 |
| embed-service | 文本→向量 | List[text] | List[vector] | 内部 / API POST /embed | E200 模型未加载 |
| vector-store | 向量增删查 | vectors+meta / query vector | hits{id,score,text} | Qdrant gRPC/REST | E300 连接失败, E301 写入失败 |
| rerank-service | 候选重排 | query, candidates | ranked list | 内部 / API POST /rerank | E400 模型未加载 |
| llm-gateway | 统一推理（local/cloud 降级） | messages / prompt | completion(stream) | 内部 / API POST /chat | E500 后端不可用, E501 超时 |
| agent-core | ReAct 规划+工具调用 | user query, tools | final answer + trace | 内部 / API POST /agent | E600 工具执行失败, E601 超步数 |
| rag-pipeline | 串联 ingest→retrieve→rerank→generate | query | answer + citations | 内部 / API POST /rag | E700 检索空, E701 生成失败 |
| api-server | REST 聚合 | HTTP | JSON | REST/OpenAPI | 标准 HTTP |
| web-ui | 聊天界面 | 用户交互 | 渲染 | HTTP/SSE | — |
| cli | 命令行入口 | argv | 文本/JSON | stdout | 进程码 |
| eval-harness | 评测 | dataset | metrics report | pytest / CLI | — |

## 4. 对标 SOTA 指标基线（目标）
| 维度 | 指标 | 目标基线 | 对标对象 | 说明 |
|---|---|---|---|---|
| 检索 | Recall@10 | ≥0.90 | naive BM25(基线) / SOTA RAG | 混合检索 vs 纯向量 |
| 检索 | nDCG@10 | +5~8pt vs 无重排 | BGE-rerank 论文 | 重排增益 |
| 嵌入 | MTEB-zh avg | 对标 BGE-M3 公开值 | BGE-M3 / bge-large-zh | 复用 SOTA 模型 |
| 生成 | RAGAS faithfulness | ≥0.85 | 无检索直答(基线) | 溯源降幻觉 |
| 生成 | answer relevancy | ≥0.90 | 无检索直答(基线) | |
| 延迟 | p95 端到端 | <3s (1 doc, 7B q4) | 同类本地 RAG | CPU bound |
| 吞吐 | local tok/s | 记录基线(量化后实测) | vLLM GPU(参考) | 注明硬件 |

## 5. 工程结构与一键复现
目录：
```
zhishu/
├─ docker-compose.yml        # 一键起全栈
├─ pyproject.toml + uv.lock  # 后端依赖锁定
├─ services/
│  ├─ api/        # FastAPI 服务
│  ├─ ingest/     # doc-ingest + embed
│  ├─ retrieval/  # vector-store + rerank
│  ├─ llm/        # llm-gateway
│  ├─ agent/      # agent-core
│  └─ eval/       # eval-harness
├─ web/           # React 前端
├─ cli/           # Typer CLI
├─ tests/         # 单测 + 最小可运行示例
├─ data/         # 示例文档 + 评测集
├─ docs/          # 架构/部署/使用
└─ scripts/setup.sh  # 一键安装/拉模型/起服务
```
一键：`docker compose up --build`；或 `scripts/setup.sh`（建 venv、装依赖、拉 Ollama 模型、起服务）。云端模式零下载即可跑（不加载本地模型）。

## 6. 里程碑与验收（DoD）
| # | 里程碑 | 验收标准 | 状态 |
|---|---|---|---|
| M1 | 环境与依赖锁定 | clean env 装通、lockfile 生成 | ✅ 完成 |
| M2 | 单模块可独立验证 | 每模块单测通过 + 最小示例 | ✅ 完成（19 单测全绿） |
| M3 | RAG 链路跑通 | 入库→检索→重排→生成，带引用 | ✅ 完成（真实 Ollama 端到端验证） |
| M4 | Agent 跑通 | 工具调用多步完成任务 | ✅ 完成（current_time/kb_search 真实 Ollama 端到端验证） |
| M5 | 三形态交付 | Web/API/CLI 均可用 | ✅ 完成（CLI 全命令 / Web 挂载 dist / API 全端点均实测通过） |
| M6 | 评测与基线 | RAGAS 报告 + 对标表 | ✅ 完成（context_recall 0.98 / faithfulness 1.0 / answer_relevancy 0.67 / 延迟 ~5.7s，本地 1.5B CPU 实测） |
| M7 | Docker 一键复现 | clone→compose up→demo 零手工 | ✅ 配置校验通过（compose config OK）；各构建步骤已分别验证（前端 npm run build 成功、uv.lock 可复现安装、应用全链路跑通）；完整镜像构建仅受本沙箱 Docker Hub 不可达（auth.docker.io 502）阻塞，标准环境/配镜像加速器即可一键复现 |
| M8 | 文档 + 推送仓库 | 架构/部署/使用齐 + GitHub 晨星 | ✅ 完成（已推送 https://github.com/CJX0712/zhishu ，作者 晨星，分支 main） |

## 7. 风险与对策
- 16GB 内存跑 7B q4 偏紧 → 默认支持 3B/1.5B 小模型，7B 可选；云端模式零本地负载。
- 模型下载体积大 → 不入库，首次 `ollama pull` 脚本化；提供云端模式免下载。
- LangGraph 版本波动 → 严格 pin；不可解则自研轻量编排并书面说明（满足"确须自研须书面说明理由"）。
- 外网/密钥 → 云端模式需用户提供 API Key（仅本地 env，不入库）；本地模式不依赖。
