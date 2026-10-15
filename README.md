# 智枢 ZhiShu

<div align="center">

[![License](https://img.shields.io/badge/License-MIT-green)](https://github.com/CJX0712/zhishu/blob/main/LICENSE) [![Language](https://img.shields.io/badge/Python-3776AB?logo=python)](https://github.com/CJX0712/zhishu) [![Author](https://img.shields.io/badge/author-晨星-blueviolet)](https://github.com/CJX0712)

</div>


企业级 AI 知识中枢与智能体平台。**本地优先、混合推理**：RAG 知识问答 + ReAct Agent 工具编排，统一以 **Web / REST API / CLI** 三种形态交付，Docker Compose 一键复现。

> 完整文档见 `docs/`（架构 / 部署 / 使用）。开工基线见 `PLAN.md`。

## 能力边界
- ✅ 多格式文档入库 → 混合检索（向量 + BM25）→ 重排 → 带引用溯源的生成
- ✅ ReAct Agent：可插拔工具（知识库检索 / 计算 / 时间）
- ✅ 混合推理：本地 Ollama 量化模型（离线可跑）+ 云端 OpenAI 兼容 API 兜底
- ❌ 不训练/微调模型；❌ 不做多模态生成；❌ 不做分布式训练

## 快速开始（一键）
```bash
docker compose up --build        # 全栈：qdrant + ollama + backend + web
# 或本地开发：
scripts/setup.sh                # 建 venv、装依赖、拉模型、起服务
```

## 最小验证（无需 GPU / 无需外网密钥）
```bash
zhishu ingest data/docs/sample.txt
zhishu ask "你们的退款政策是什么？"
```

作者：晨星
