from zhishu.llm import LLMError, OpenAIGateway


class FakeCompletions:
    def create(self, **kw):
        class M:
            def __init__(self, c):
                self.content = c

        class Ch:
            def __init__(self, c):
                self.message = M(c)

        class R:
            def __init__(self, c):
                self.choices = [Ch(c)]

        msg = kw["messages"][-1]["content"]
        return R(f"回复：{msg[:15]}")


class FakeChat:
    completions = FakeCompletions()


class FakeClient:
    def __init__(self, *a, **k):
        self.chat = FakeChat()


class FakeChunk:
    def __init__(self, c):
        class Delta:
            def __init__(self, cc):
                self.content = cc

        class Ch:
            def __init__(self, cc):
                self.delta = Delta(cc)

        self.choices = [Ch(c)]


class FakeStreamCompletions:
    def create(self, **kw):
        for w in ["你好", "世界"]:
            yield FakeChunk(w)


class FakeStreamChat:
    completions = FakeStreamCompletions()


class FakeStreamClient:
    def __init__(self, *a, **k):
        self.chat = FakeStreamChat()


def test_gateway_local():
    g = OpenAIGateway()
    g.s.llm_mode = "local"
    g._local_client = lambda: FakeClient()
    out = g.complete([{"role": "user", "content": "你好"}])
    assert "回复" in out


def test_gateway_stream():
    g = OpenAIGateway()
    g.s.llm_mode = "local"
    g._local_client = lambda: FakeStreamClient()
    toks = list(g.stream([{"role": "user", "content": "hi"}]))
    assert toks == ["你好", "世界"]


def test_gateway_cloud_key_missing():
    g = OpenAIGateway()
    g.s.llm_mode = "cloud"
    g.s.llm_cloud_api_key = ""
    g._local = None
    g._cloud = None
    try:
        g.complete([{"role": "user", "content": "hi"}])
        assert False, "应抛出 LLMError"
    except LLMError:
        pass
