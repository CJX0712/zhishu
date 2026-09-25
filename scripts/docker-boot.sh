#!/usr/bin/env bash
# 容器一键部署：构建并起全栈，自动拉模型 + 入库示例
set -e
cd "$(dirname "$0")/.."

echo "==> 构建并启动 qdrant / ollama / backend"
docker compose up -d --build

echo "==> 等待 Ollama 就绪"
until curl -s --noproxy '*' http://localhost:11434/ >/dev/null 2>&1; do sleep 2; done

echo "==> 拉取本地模型（首次需下载，可随时 Ctrl-C 跳过改用云端）"
docker compose exec -T ollama ollama pull "${ZHISHU_LLM_LOCAL_MODEL:-qwen2.5:1.5b}" || true

echo "==> 入库示例文档"
docker compose exec -T backend zhishu ingest data/docs/sample.txt || true

echo "==> 完成。打开 http://localhost:8000"
