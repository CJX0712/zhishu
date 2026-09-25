"""命令行入口（Typer）：ingest / ask / agent / search / health / reset / eval / serve / version。"""
from __future__ import annotations
import json
import os

import typer

from . import __version__, agent as agent_mod, eval as eval_mod, rag, retriever
from . import ingest as ingest_mod
from .config import get_settings
from .llm import LLMError
from .vector_store import count, reset_collection

app = typer.Typer(help="智枢 ZhiShu CLI", no_args_is_help=True)


@app.command()
def ingest(path: str, source: str = typer.Option(None, "--source")):
    """入库文件或目录（按扩展名自动选择解析器）。"""
    if os.path.isdir(path):
        n = ingest_mod.ingest_directory(path)
    else:
        n = ingest_mod.ingest_file(path, source=source)
    typer.echo(f"已入库 {n} 块")


@app.command()
def ask(query: str, stream: bool = False):
    """RAG 问答。"""
    if stream:
        out = rag.answer_stream(query)
        for tok in out["stream"]:
            typer.echo(tok, nl=False)
        typer.echo()
        return
    try:
        res = rag.answer(query)
    except LLMError as e:
        typer.echo(f"错误: {e}")
        raise typer.Exit(1)
    typer.echo(res["answer"])
    if res["citations"]:
        typer.echo("\n引用:")
        for c in res["citations"]:
            typer.echo(f"  [{c['index']}] {c['source']}")


@app.command()
def agent(query: str):
    """Agent 多步推理（工具调用）。"""
    res = agent_mod.run_agent(query)
    typer.echo(res["answer"])
    typer.echo("\nTrace:")
    for t in res["trace"]:
        if "action" in t:
            typer.echo(f"  step{t['step']} Action={t['action']} -> {t['observation'][:120]}")
        else:
            typer.echo(f"  step{t['step']} Final: {t.get('final','')[:120]}")


@app.command()
def search(query: str, top_k: int = 5):
    """仅检索，返回候选上下文。"""
    res = retriever.retrieve(query, top_k=top_k)
    for i, c in enumerate(res):
        typer.echo(f"[{i + 1}] ({c['score']:.3f}) {c['text'][:120]}")


@app.command()
def health():
    """健康检查与文档数。"""
    typer.echo(f"status=ok docs={count()}")


@app.command()
def reset():
    """清空知识库。"""
    reset_collection()
    typer.echo("已清空知识库")


@app.command()
def eval(
    dataset: str = typer.Argument("data/eval/sample.json"),
    out: str = typer.Argument("data/eval/report.json"),
):
    """运行评测并输出指标摘要。"""
    try:
        report = eval_mod.run_eval(dataset, out)
    except FileNotFoundError as e:
        typer.echo(f"评测集不存在: {e}")
        raise typer.Exit(1)
    typer.echo(json.dumps(report["summary"], ensure_ascii=False, indent=2))


@app.command()
def serve(host: str = None, port: int = None):
    """启动 REST API 服务。"""
    import uvicorn

    s = get_settings()
    uvicorn.run(
        "zhishu.api:app",
        host=host or s.api_host,
        port=port or s.api_port,
        log_level=s.log_level,
    )


@app.command()
def version():
    """显示版本。"""
    typer.echo(f"zhishu {__version__}  ·  作者 晨星")


if __name__ == "__main__":
    app()
