from bancobot.agent import BancoAgentBuilder
from langchain.agents.middleware import ModelRequest
from langchain.agents.middleware.types import ModelResponse


class DummyDoc:
    def __init__(self, content: str):
        self.page_content = content


class DummyVectorStore:
    def __init__(self, docs: list[DummyDoc]):
        self._docs = docs
        self.queries: list[str] = []

    def similarity_search(self, query: str):
        self.queries.append(query)
        return list(self._docs)


class DummyStateMsg:
    def __init__(self, text: str):
        self.text = text


def test_no_rag_returns_builder():
    from fork_engine.twinbots.no_rag import no_rag

    builder = no_rag()

    assert isinstance(builder, BancoAgentBuilder)
    # no_rag() intentionally does not wire tools/middlewares
    assert builder.toolkit is None
    assert builder.middlewares is None


def test_single_rag_tool_builds_one_tool_and_uses_vector_store(monkeypatch):
    from fork_engine.twinbots import single_tool

    vs = DummyVectorStore([DummyDoc("doc-a"), DummyDoc("doc-b")])
    monkeypatch.setattr(single_tool, "get_vector_store", lambda: vs)

    builder = single_tool.single_rag_tool()

    assert isinstance(builder, BancoAgentBuilder)
    assert builder.toolkit is not None
    assert len(builder.toolkit) == 1

    tool = builder.toolkit[0]
    res = tool.invoke("hello")

    assert vs.queries == ["hello"]
    assert res == "doc-a\n\ndoc-b"


def test_two_step_rag_configures_prompt_middleware_and_no_tools():
    from fork_engine.twinbots.two_step import prompt_with_context, two_step_rag

    builder = two_step_rag()

    assert isinstance(builder, BancoAgentBuilder)
    assert builder.toolkit == []
    assert builder.middlewares is not None
    assert builder.middlewares == [prompt_with_context]


def test_prompt_with_context_injects_docs_into_system_prompt(monkeypatch):
    from fork_engine.twinbots import two_step

    vs = DummyVectorStore([DummyDoc("ctx-1"), DummyDoc("ctx-2")])
    monkeypatch.setattr(two_step, "get_vector_store", lambda: vs)

    # the middleware reads the last query from request.state["messages"][-1].text
    req = ModelRequest(
        model="gpt-4.1",  # pyright: ignore[reportArgumentType]
        messages=[],
        state={"messages": [DummyStateMsg("qual o melhor cartão?")]},  # pyright: ignore[reportArgumentType]
    )

    seen = {}

    def handler(r: ModelRequest):
        seen["system_prompt"] = r.system_prompt
        return ModelResponse(result=[])

    _res = two_step.prompt_with_context.wrap_model_call(req, handler)

    assert vs.queries == ["qual o melhor cartão?"]

    system_prompt = seen.get("system_prompt")
    assert isinstance(system_prompt, str)
    assert "Responda exclusivamente com base no contexto" in system_prompt
    assert "ctx-1" in system_prompt
    assert "ctx-2" in system_prompt


def test_triple_rag_tool_builds_three_tools_with_expected_collections(monkeypatch):
    from fork_engine.twinbots import triple_tool

    created: dict[str, DummyVectorStore] = {}
    calls: list[str] = []

    def fake_get_vector_store(collection: str = "banco_collection"):
        calls.append(collection)
        vs = DummyVectorStore(
            [DummyDoc(f"{collection}-1"), DummyDoc(f"{collection}-2")]
        )
        created[collection] = vs
        return vs

    monkeypatch.setattr(triple_tool, "get_vector_store", fake_get_vector_store)

    builder = triple_tool.triple_rag_tool()

    assert isinstance(builder, BancoAgentBuilder)
    assert builder.toolkit is not None
    assert len(builder.toolkit) == 3

    assert calls == [
        "cartoes_collection",
        "varejo_collection",
        "milhas_collection",
    ]

    # Ensure each tool is bound to its own vector store instance
    results = [tool.invoke("pergunta") for tool in builder.toolkit]
    assert created["cartoes_collection"].queries == ["pergunta"]
    assert created["varejo_collection"].queries == ["pergunta"]
    assert created["milhas_collection"].queries == ["pergunta"]

    # And that outputs came from their respective stores
    assert results[0] == "cartoes_collection-1\n\ncartoes_collection-2"
    assert results[1] == "varejo_collection-1\n\nvarejo_collection-2"
    assert results[2] == "milhas_collection-1\n\nmilhas_collection-2"
