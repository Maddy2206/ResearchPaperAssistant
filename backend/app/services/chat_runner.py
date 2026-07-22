import asyncio
import uuid

from app.agents.aggregate import aggregate_node
from app.db.crud_chat import add_message, recent_history
from app.db.models import MessageRole
from app.db.session import AsyncSessionLocal
from app.graph.workflow import SPECIALIST_NODES
from app.services.events import close, publish


def spawn_chat_run(
    *,
    conversation_id: uuid.UUID,
    paper_id: uuid.UUID,
    user_query: str,
    run_id: str,
    forced_agent: str,
) -> None:
    asyncio.create_task(_run(conversation_id, paper_id, user_query, run_id, forced_agent))


async def _run(
    conversation_id: uuid.UUID,
    paper_id: uuid.UUID,
    user_query: str,
    run_id: str,
    forced_agent: str,
) -> None:
    try:
        async with AsyncSessionLocal() as db:
            history = await recent_history(db, conversation_id)

        initial_state = {
            "paper_id": str(paper_id),
            "conversation_id": str(conversation_id),
            "run_id": run_id,
            "user_query": user_query,
            "chat_history": history,
            "agent_outputs": [],
            "errors": [],
        }

        # Each conversation is pinned to one agent tab, so route straight to
        # that specialist and skip the orchestrator's router/fan-out entirely.
        node_fn = SPECIALIST_NODES[forced_agent]
        node_output = await node_fn(initial_state)
        final_state = await aggregate_node({**initial_state, **node_output})

        content = final_state.get("final_answer") or "I couldn't generate a response."
        citations = final_state.get("final_citations", [])
        agents_used = final_state.get("final_agents_used", [])

        async with AsyncSessionLocal() as db:
            message = await add_message(
                db,
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=content,
                agent_used=agents_used,
                citations=citations,
            )

        await publish(
            run_id,
            {
                "event": "message_completed",
                "run_id": run_id,
                "message_id": str(message.id),
                "content": content,
                "citations": citations,
                "agents_used": agents_used,
            },
        )
    except Exception as exc:  # noqa: BLE001
        await publish(run_id, {"event": "error", "run_id": run_id, "error": str(exc)})
    finally:
        await close(run_id)
