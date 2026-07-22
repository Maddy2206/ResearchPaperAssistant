import uuid
from typing import TypeVar

from pydantic import BaseModel

from app.db.session import AsyncSessionLocal
from app.llm.client import LLMClient, get_llm_client
from app.llm.prompts import format_sources
from app.retrieval.search import similarity_search
from app.services.events import publish

T = TypeVar("T", bound=BaseModel)


async def run_agent(
    run_id: str,
    agent_key: str,
    system: str,
    user: str,
    schema: type[T],
    llm: LLMClient | None = None,
) -> T | None:
    """Discrete structured-output call (used by the router and any agent step
    that needs a JSON payload). Emits SSE lifecycle events and degrades
    gracefully — returns None on failure rather than raising, so a single
    agent's failure doesn't crash the whole graph run."""
    client = llm or get_llm_client()
    await publish(run_id, {"event": "agent_started", "agent": agent_key, "run_id": run_id})
    try:
        result = await client.structured(system, user, schema)
        await publish(run_id, {"event": "agent_completed", "agent": agent_key, "run_id": run_id})
        return result
    except Exception as exc:  # noqa: BLE001
        await publish(
            run_id, {"event": "agent_failed", "agent": agent_key, "run_id": run_id, "error": str(exc)}
        )
        return None


async def stream_agent(
    run_id: str,
    agent_key: str,
    system: str,
    user: str,
    citations: list[dict],
    llm: LLMClient | None = None,
) -> dict | None:
    """Streams a prose answer token-by-token over SSE, accumulating the full
    text. Returns {"agent": agent_key, "content": ..., "citations": [...]}
    on success, None on failure (graceful per-agent degradation)."""
    client = llm or get_llm_client()
    await publish(run_id, {"event": "agent_started", "agent": agent_key, "run_id": run_id})
    accumulated = ""
    try:
        async for delta in client.stream_chat(system, user):
            accumulated += delta
            await publish(
                run_id,
                {"event": "token", "agent": agent_key, "run_id": run_id, "content": delta},
            )
        await publish(run_id, {"event": "agent_completed", "agent": agent_key, "run_id": run_id})
        return {"agent": agent_key, "content": accumulated, "citations": citations}
    except Exception as exc:  # noqa: BLE001
        await publish(
            run_id, {"event": "agent_failed", "agent": agent_key, "run_id": run_id, "error": str(exc)}
        )
        return None


async def run_specialist(
    run_id: str,
    agent_key: str,
    paper_id: str,
    query: str,
    system_prompt: str,
) -> dict:
    """Shared retrieve-then-stream flow used by every specialist leaf node:
    runs agent-aware similarity search, formats a numbered source list local
    to this agent's own answer, then streams the prose response."""
    async with AsyncSessionLocal() as db:
        sources = await similarity_search(
            db, paper_id=uuid.UUID(paper_id), query=query, agent_key=agent_key
        )

    citations = [
        {
            "index": i,
            "chunk_id": str(s["chunk_id"]),
            "page_number": s["page_number"],
            "section_title": s["section_title"],
            "content_type": s["content_type"],
            "snippet": s["text"][:280],
        }
        for i, s in enumerate(sources, start=1)
    ]

    user_prompt = f"Source excerpts:\n{format_sources(sources)}\n\nUser question: {query}"

    output = await stream_agent(run_id, agent_key, system_prompt, user_prompt, citations)
    if output is None:
        return {
            "agent_outputs": [
                {
                    "agent": agent_key,
                    "content": (
                        f"_The {agent_key.replace('_', ' ')} agent failed to respond. "
                        "Please try again._"
                    ),
                    "citations": [],
                }
            ]
        }
    return {"agent_outputs": [output]}
