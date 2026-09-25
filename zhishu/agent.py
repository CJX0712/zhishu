"""Agent 编排：轻量 ReAct（推理-行动-观察）循环，工具可插拔。

设计说明：采用自研最小 ReAct 实现而非 LangGraph，避免其重量级且版本敏感的依赖树，
保证干净环境一键复现；接口清晰、可单测，符合「能复用不重写、确须自研须书面说明理由」。
"""
from __future__ import annotations
import inspect
import re
from typing import Optional

from .llm import LLM, OpenAIGateway
from .tools import TOOLS


def _call_tool(func, ainput: str) -> str:
    """调用工具函数，兼容「无参工具」（如 current_time）与「需参工具」。

    某些工具（current_time）定义为无参函数；Agent 默认会把解析出的 Action Input
    作为参数传入，无参函数会报 TypeError。此处通过签名内省，无参则不传参，
    同时兼容无法内省的 lambda/内置对象（先尝试传参，失败再无参）。
    """
    try:
        params = inspect.signature(func).parameters.values()
        positional = [p for p in params if p.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )]
        if not positional:
            return str(func())
        return str(func(ainput))
    except (TypeError, ValueError):
        # 无法内省签名：先尝试传参，失败则无参调用
        try:
            return str(func(ainput))
        except TypeError:
            return str(func())

AGENT_SYSTEM = """你是一个可以使用工具的智能助手。可用工具：
{tool_desc}

当需要事实性信息（当前时间、知识库内容、数值计算）时，必须先调用对应工具，再基于 Observation 作答，不得编造。
严格按以下格式推理与行动（每次只选一个 Action）：
Thought: 你的思考
Action: 工具名（必须是 {tools} 之一）
Action Input: 工具参数（字符串；无参数写 None）
Observation: （系统自动填充工具结果）
... 重复 Thought/Action/Observation，直到能回答，然后输出：
Thought: 我已获得足够信息
Final Answer: 给最终用户的完整回答

示例：
用户问题：现在几点？
Thought: 需要获取当前时间，应调用 current_time 工具。
Action: current_time
Action Input: None
Observation: 2026-09-25 21:30:00
Thought: 已获得时间，可以作答。
Final Answer: 现在是 2026-09-25 21:30:00。"""


def _tool_desc(tools: dict) -> str:
    return "\n".join(f"- {n}: {t['description']}" for n, t in tools.items())


def parse_action(text: str) -> dict:
    # 动作优先：只要出现 Action 就执行，避免小模型在同一条消息里顺带写出
    # Final Answer 时提前终止、跳过工具调用。
    action_m = re.search(r"Action:\s*(.+)", text)
    input_m = re.search(r"Action Input:\s*(.+)", text)
    if action_m:
        action = action_m.group(1).strip()
        ainput = input_m.group(1).strip() if input_m else "None"
        ainput = "" if ainput.lower() == "none" else ainput
        return {"type": "action", "action": action, "input": ainput}
    final_m = re.search(r"Final Answer:\s*(.+)", text, re.S)
    if final_m:
        return {"type": "final", "value": final_m.group(1).strip()}
    return {"type": "final", "value": text.strip()}


def run_agent(
    query: str,
    llm: Optional[LLM] = None,
    tools: Optional[dict] = None,
    max_steps: int = 5,
) -> dict:
    tools = tools or TOOLS
    llm = llm or OpenAIGateway()
    trace: list[dict] = []
    system = AGENT_SYSTEM.format(
        tool_desc=_tool_desc(tools), tools=", ".join(tools.keys())
    )
    history = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"用户问题：{query}"},
    ]
    for step in range(1, max_steps + 1):
        resp = llm.complete(history)
        parsed = parse_action(resp)
        if parsed["type"] == "final":
            trace.append({"step": step, "final": parsed["value"]})
            return {"answer": parsed["value"], "trace": trace, "steps": step}
        action = parsed.get("action", "")
        ainput = parsed.get("input", "")
        tool = tools.get(action)
        if tool is None:
            observation = f"未知工具：{action}。可用工具：{', '.join(tools.keys())}。"
        else:
            try:
                observation = _call_tool(tool["func"], ainput)
            except Exception as e:  # noqa: BLE001
                observation = f"工具执行出错: {e}"
        trace.append({"step": step, "action": action, "input": ainput, "observation": observation})
        history.append({"role": "assistant", "content": resp})
        history.append({"role": "user", "content": f"Observation: {observation}"})
    return {
        "answer": "已达到最大步数仍未得出最终答案。",
        "trace": trace,
        "steps": max_steps,
    }
