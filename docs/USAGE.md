# 使用指南（Usage）

系统提供三种等价入口，底层共用同一套服务模块。

## A. Web（http://localhost:8000）
- 顶部切换「RAG 问答 / Agent 推理」。
- 输入问题回车发送，回答下方展示引用来源 `[1] 文件名`。

## B. CLI（Typer）
```bash
# 入库
zhishu ingest data/docs/sample.txt
zhishu ingest ./我的文档目录        # 递归目录

# 问答
zhishu ask "标准发货后几天内可以全额退款？"
zhishu ask --stream "..."          # 流式输出

# Agent（工具调用）
zhishu agent "请查阅知识库，年假怎么算？"

# 检索（仅看召回）
zhishu search "退款政策" --top-k 3

# 评测
zhishu eval data/eval/sample.json

# 服务 / 健康检查
zhishu serve                       # uvicorn 起 8000
zhishu health
zhishu reset                      # 清空知识库
```

## C. REST API（FastAPI，自动文档 http://localhost:8000/docs）
```bash
# 入库
curl -X POST http://localhost:8000/api/ingest \
  -H 'Content-Type: application/json' \
  -d '{"text":"年假满1年5天。"}'

# RAG 问答
curl -X POST http://localhost:8000/api/rag \
  -H 'Content-Type: application/json' \
  -d '{"query":"年假怎么算？"}'

# Agent
curl -X POST http://localhost:8000/api/agent \
  -H 'Content-Type: application/json' \
  -d '{"query":"现在几点？请用工具查时间"}'

# 检索 / 健康
curl -X POST http://localhost:8000/api/search -H 'Content-Type: application/json' -d '{"query":"退款"}'
curl http://localhost:8000/api/health
```

## 自定义知识库
将企业文档（txt/md/json/html/pdf）放入目录，`zhishu ingest <目录>` 即可；检索与生成自动基于新内容。

## 接入新工具（Agent）
在 `zhishu/tools.py` 的 `TOOLS` 增加一项 `{description, func}`，Agent 即可在 ReAct 循环中调用。

## 离线 / 内网部署（嵌入模型）
默认嵌入模型 `BAAI/bge-small-zh-v1.5` 首次使用会从 HuggingFace 下载。无外网或需复用已下载模型时，可指定本地目录（含 `model_optimized.onnx` / `tokenizer.json` / `tokenizer_config.json` / `config.json`）：

```bash
export ZHISHU_EMBED_MODEL_PATH=/path/to/bge-small-zh-v1.5
# 或写入 .env
```

设置后 `embeddings` 模块通过 `specific_model_path` 直接加载，跳过下载。其余联网组件（Ollama 本地模型、云端兜底 API）不受影响。
