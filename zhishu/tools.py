"""Agent 工具集（可插拔）。每个工具：{description, func}。"""
from __future__ import annotations
import re
from datetime import datetime


def kb_search(query: str, top_k: int = 3) -> str:
    from .retriever import retrieve

    res = retrieve(query)
    if not res:
        return "知识库暂无相关内容。"
    return "\n".join(f"[{i + 1}] {c['text']}" for i, c in enumerate(res[:top_k]))


_SAFE_BUILTINS = {"abs": abs, "round": round, "min": min, "max": max, "pow": pow,
                  "float": float, "int": int, "len": len, "sum": sum}


def calculator(expr: str) -> str:
    expr = str(expr).strip()
    if not re.fullmatch(r"[0-9+\-*/().% ,]*", expr):
        return "仅支持数字与 + - * / % ( ) 运算。"
    try:
        return str(eval(expr, {"__builtins__": {}}, _SAFE_BUILTINS))  # noqa: S307
    except Exception as e:  # noqa: BLE001
        return f"计算错误: {e}"


def current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


TOOLS: dict[str, dict] = {
    "kb_search": {
        "description": "在企业知识库中检索资料。参数 query：检索问题（字符串）。",
        "func": kb_search,
    },
    "calculator": {
        "description": "计算数学表达式。参数 expr：如 '23*45+10'。",
        "func": calculator,
    },
    "current_time": {
        "description": "返回当前系统时间。无需参数。",
        "func": current_time,
    },
}
