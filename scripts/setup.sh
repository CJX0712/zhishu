#!/usr/bin/env bash
# 本地一键部署（开发态）：建 venv → 装依赖 →（可选）拉本地模型 → 入库示例 → 起服务
set -e
cd "$(dirname "$0")/.."

echo "==> 创建虚拟环境并安装依赖"
if ! command -v uv >/dev/null 2>&1; then
  pip install uv
fi
uv venv 2>/dev/null || true
if [ -f .venv/bin/activate ]; then source .venv/bin/activate; else source .venv/Scripts/activate; fi
uv sync --extra dev

echo "==> 拉取本地推理模型（可选，跳过则使用云端兜底）"
if command -v ollama >/dev/null 2>&1; then
  ollama pull "${ZHISHU_LLM_LOCAL_MODEL:-qwen2.5:1.5b}" || true
fi

echo "==> 入库示例知识库"
zhishu ingest data/docs/sample.txt

echo "==> 完成。启动服务： zhishu serve  然后访问 http://localhost:8000"
