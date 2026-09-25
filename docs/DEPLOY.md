# 部署指南（Deployment）

## 方式一：Docker 一键（推荐，零本地 Python 环境）
```bash
# 1) 起全栈（qdrant + ollama + backend 含前端）
docker compose up -d --build

# 2) 首次拉取本地推理模型（约 1GB，可跳过改用云端）
docker compose exec -T ollama ollama pull qwen2.5:1.5b

# 3) 入库示例知识库
docker compose exec -T backend zhishu ingest data/docs/sample.txt

# 4) 打开 http://localhost:8000
```
或用封装脚本：`bash scripts/docker-boot.sh`（自动完成 1–3）。

> **镜像加速（Docker Hub 不可达时）**：在国内/受限网络，可在 Docker Desktop 的 `daemon.json` 配置 `registry-mirrors`（如 `https://docker.1panel.live`、`https://docker.m.daocloud.io` 等），使 `node:20-slim` / `python:3.11-slim` 等基础镜像可正常拉取；或先 `docker pull` 基础镜像后离线构建。

> **零下载模式**：不拉本地模型，改用云端兜底。编辑 `docker-compose.yml` 的 `backend.environment`，设 `ZHISHU_LLM_MODE=cloud` 与 `ZHISHU_LLM_CLOUD_API_KEY=...`，即可完全免模型下载运行。

## 方式二：本地开发
```bash
bash scripts/setup.sh        # 建 venv、装依赖、拉模型、入库示例
zhishu serve                 # 启动 API，浏览器开 http://localhost:8000
```
> 本地若已有 Ollama，先 `OLLAMA_HOST=127.0.0.1:11434 ollama serve`，再设 `ZHISHU_LLM_LOCAL_BASE_URL`。

## 环境变量（前缀 ZHISHU_，详见 `.env.example`）
| 变量 | 说明 | 默认 |
|---|---|---|
| `ZHISHU_LLM_MODE` | local / cloud / hybrid | hybrid |
| `ZHISHU_LLM_LOCAL_BASE_URL` | Ollama 端点 | http://localhost:11434/v1 |
| `ZHISHU_LLM_LOCAL_MODEL` | 本地模型名 | qwen2.5:1.5b |
| `ZHISHU_LLM_CLOUD_API_KEY` | 云端 Key（仅 cloud/hybrid 兜底） | 空 |
| `ZHISHU_EMBED_MODEL` | 嵌入模型 | BAAI/bge-small-zh-v1.5 |
| `ZHISHU_EMBED_MODEL_PATH` | 本地离线模型目录（跳过 HF 下载） | 空（自动下载） |
| `ZHISHU_QDRANT_HOST/PORT` | 向量库地址 | localhost:6333 |
| `ZHISHU_COLLECTION_NAME` | 集合名 | zhishu_docs |
| `ZHISHU_RETRIEVAL_TOP_K / FINAL_TOP_K` | 召回/终选数量 | 20 / 5 |

## 资源建议
- 本地 1.5b q4 模型约 1GB 显存/内存，CPU 可跑（慢）；7b 建议 8GB+ 显存。
- 嵌入模型首次运行自动下载（~130MB）。
- 16GB 内存机器建议用 1.5b 或云端模式；7b 可选。
