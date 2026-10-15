# 智枢 ZhiShu

<div align="center">

[![CI](https://github.com/CJX0712/zhishu/actions/workflows/ci.yml/badge.svg)](https://github.com/CJX0712/zhishu/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-MIT-green)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)](https://github.com/CJX0712/zhishu)
[![Author](https://img.shields.io/badge/author-晨星-blueviolet)](https://github.com/CJX0712)

**企业级 AI 知识中枢与智能体平台 · 本地优先 · 混合推理**

</div>

RAG 知识问答 + ReAct Agent 工具编排，统一以 **Web / REST API / CLI** 三种形态交付，Docker Compose 一键复现。

设计取向：**Provider 可注入、链路可离线跑、答案带溯源**。默认零密钥——本地 Ollama 量化模型推理，云端 OpenAI 兼容接口作为可选兜底。

---

## 能力边界

| 支持 | 不支持 |
| --- | --- |
| ✅ 多格式文档入库 → 混合检索（向量 + BM25）→ 重排 → 带引用溯源的生成 | ❌ 训练 / 微调模型 |
| ✅ ReAct Agent：可插拔工具（知识库检索 / 计算 / 时间） | ❌ 多模态生成 |
| ✅ 混合推理：本地 Ollama（离线可跑）+ 云端 OpenAI 兼容 API 兜底 | ❌ 分布式训练 |
| ✅ 三种交付形态共用同一套核心（Web / REST API / CLI） | ❌ 托管服务 |

---

## 架构

一次问答的完整链路，每层单一职责、可独立替换：

```
文档 → ingest → embeddings → retriever(向量+BM25 混合) → rerank → rag(带引用生成)
                                                             ↑
                                              agent(ReAct) → tools
                                                             ↓
                                              api / cli / web 三形态出口
```

| 模块 | 文件 | 职责 |
| --- | --- | --- |
| 配置 | `zhishu/config.py` | 环境驱动的配置注入，provider 可切换 |
| 入库 | `zhishu/ingest.py` | 多格式解析 → 分块 → 落库 |
| 向量化 | `zhishu/embeddings.py` | 嵌入抽象，本地/云端双后端 |
| 检索 | `zhishu/retriever.py` | 向量 + BM25 混合召回 |
| 重排 | `zhishu/rerank.py` | 候选精排 |
| 生成 | `zhishu/rag.py` | 带引用溯源的答案合成 |
| 智能体 | `zhishu/agent.py` · `zhishu/tools.py` | ReAct 循环 + 可插拔工具 |
| 模型层 | `zhishu/llm.py` | OpenAI 兼容 / Ollama / 确定性 mock |
| 出口 | `zhishu/api.py` · `zhishu/cli.py` · `web/` | FastAPI 服务 / 命令行 / 前端 |
| 评测 | `zhishu/eval.py` | 检索与答案质量评测 |

---

## 快速开始

**Docker（全栈一键）**

```bash
docker compose up --build      # qdrant + ollama + backend + web
```

**本地开发**

```bash
scripts/setup.sh               # 建 venv、装依赖、拉模型、起服务
```

**最小验证（无需 GPU、无需外网密钥）**

```bash
zhishu ingest data/docs/sample.txt
zhishu ask "你们的退款政策是什么？"
```

---

## 验证

```bash
pytest tests/ -q
```

测试按层独立覆盖：`test_ingest` · `test_retriever` · `test_rerank` · `test_rag` · `test_agent` · `test_api` · `test_llm`。CI 在每次 push 后于干净环境重跑，绿色由机器给出而非自述。

---

## 文档

| 文档 | 内容 |
| --- | --- |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 分层设计与模块契约 |
| [docs/USAGE.md](docs/USAGE.md) | 三种形态的用法 |
| [docs/DEPLOY.md](docs/DEPLOY.md) | 部署与运维 |
| [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md) | 验收标准 |
| [PLAN.md](PLAN.md) | 开工基线与里程碑 |

---

## 许可与署名

MIT · 作者：**晨星 · Chen Xing**（[@CJX0712](https://github.com/CJX0712)）
