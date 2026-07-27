from app.agents.aggregate import aggregate_node
from app.agents.base import stream_agent
from app.agents.router import RouteDecision, router_node


class FakeLLMClient:
    """Test double matching LLMClient's interface — never touches the network."""

    def __init__(self, structured_result=None, structured_error=None, stream_chunks=None, stream_error=None):
        self.structured_result = structured_result
        self.structured_error = structured_error
        self.stream_chunks = stream_chunks or []
        self.stream_error = stream_error

    async def structured(self, system, user, schema, **kwargs):
        if self.structured_error:
            raise self.structured_error
        return self.structured_result

    async def chat(self, system, user, **kwargs):
        return "".join(self.stream_chunks)

    async def stream_chat(self, system, user, **kwargs):
        if self.stream_error:
            raise self.stream_error
        for chunk in self.stream_chunks:
            yield chunk


def _patch_llm(monkeypatch, client: FakeLLMClient):
    monkeypatch.setattr("app.agents.base.get_llm_client", lambda: client)


# --- router_node ---


async def test_router_node_returns_route_from_llm(monkeypatch):
    _patch_llm(
        monkeypatch,
        FakeLLMClient(
            structured_result=RouteDecision(
                agents=["math_algorithm"], reasoning="asks about an equation"
            )
        ),
    )

    state = {
        "run_id": "test-run",
        "user_query": "Explain equation 3 step by step.",
        "chat_history": [],
    }
    result = await router_node(state)

    assert result["route"] == ["math_algorithm"]
    assert "equation" in result["routing_reasoning"]


async def test_router_node_dedupes_repeated_agents(monkeypatch):
    _patch_llm(
        monkeypatch,
        FakeLLMClient(
            structured_result=RouteDecision(
                agents=["math_algorithm", "math_algorithm"], reasoning="dup"
            )
        ),
    )

    state = {"run_id": "test-run", "user_query": "q", "chat_history": []}
    result = await router_node(state)

    assert result["route"] == ["math_algorithm"]


async def test_router_node_falls_back_to_general_qa_on_llm_failure(monkeypatch):
    _patch_llm(monkeypatch, FakeLLMClient(structured_error=RuntimeError("provider outage")))

    state = {"run_id": "test-run", "user_query": "hello", "chat_history": []}
    result = await router_node(state)

    assert result["route"] == ["general_qa"]


# --- stream_agent ---


async def test_stream_agent_accumulates_tokens_and_attaches_citations():
    client = FakeLLMClient(stream_chunks=["The ", "answer ", "is 42."])
    citations = [{"index": 1, "chunk_id": "abc", "page_number": 3}]

    result = await stream_agent(
        "test-run", "research_analysis", "system", "user", citations, llm=client
    )

    assert result["agent"] == "research_analysis"
    assert result["content"] == "The answer is 42."
    assert result["citations"] == citations


async def test_stream_agent_returns_none_on_provider_failure():
    client = FakeLLMClient(stream_error=ConnectionError("connection refused"))

    result = await stream_agent("test-run", "math_algorithm", "system", "user", [], llm=client)

    assert result is None


# --- aggregate_node ---


async def test_aggregate_node_single_output_passthrough():
    state = {
        "agent_outputs": [
            {"agent": "research_analysis", "content": "Summary text.", "citations": [{"index": 1}]}
        ]
    }
    result = await aggregate_node(state)

    assert result["final_answer"] == "Summary text."
    assert result["final_agents_used"] == ["research_analysis"]
    assert result["final_citations"] == [{"index": 1}]


async def test_aggregate_node_merges_multiple_outputs_under_headers():
    state = {
        "agent_outputs": [
            {"agent": "math_algorithm", "content": "The equation means X.", "citations": []},
            {"agent": "architecture_flowchart", "content": "```mermaid\ngraph TD\n```", "citations": []},
        ]
    }
    result = await aggregate_node(state)

    assert "Math & Algorithm" in result["final_answer"]
    assert "Architecture & Flowchart" in result["final_answer"]
    assert "```mermaid" in result["final_answer"]
    assert result["final_agents_used"] == ["math_algorithm", "architecture_flowchart"]


async def test_aggregate_node_handles_empty_outputs():
    result = await aggregate_node({"agent_outputs": []})

    assert result["final_agents_used"] == []
    assert result["final_answer"]
