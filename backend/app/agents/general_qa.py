from app.agents.base import run_specialist
from app.agents.state import ChatState
from app.llm.prompts import AGENT_SYSTEM_PROMPTS

AGENT_KEY = "general_qa"


async def general_qa_node(state: ChatState) -> dict:
    return await run_specialist(
        state["run_id"],
        AGENT_KEY,
        state["paper_id"],
        state["user_query"],
        AGENT_SYSTEM_PROMPTS[AGENT_KEY],
    )
