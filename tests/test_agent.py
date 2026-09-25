from zhishu import agent as agent_mod


class ScriptedLLM:
    def __init__(self, script):
        self.script = list(script)
        self.i = 0

    def complete(self, messages, model=None):
        out = self.script[self.i]
        self.i += 1
        return out

    def stream(self, messages, model=None):
        yield self.complete(messages)


def test_agent_tool_use():
    llm = ScriptedLLM([
        "Thought: 需要当前时间\nAction: current_time\nAction Input: None",
        "Thought: 已获得时间\nFinal Answer: 现在是脚本时间。",
    ])
    tools = {"current_time": {"description": "t", "func": lambda: "2026-01-01 00:00:00"}}
    res = agent_mod.run_agent("现在几点？", llm=llm, tools=tools)
    assert res["answer"] == "现在是脚本时间。"
    assert any("current_time" in str(t.get("action", "")) for t in res["trace"])
    assert res["steps"] == 2


def test_agent_no_tool_needed():
    llm = ScriptedLLM(["Final Answer: 直接回答。"])
    res = agent_mod.run_agent("你好", llm=llm, tools={})
    assert res["answer"] == "直接回答。"
