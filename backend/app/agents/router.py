from typing import Literal

from pydantic import BaseModel, Field

from app.agents.base import run_agent
from app.agents.state import ChatState
from app.llm.prompts import ROUTER_SYSTEM_PROMPT

AgentKey = Literal[
    "research_analysis",
    "math_algorithm",
    "results_critique",
    "paper_to_code",
    "architecture_flowchart",
    "general_qa",
]


class RouteDecision(BaseModel):
    agents: list[AgentKey] = Field(description="One or more specialist agent keys to invoke")
    reasoning: str = Field(description="Brief reasoning for the chosen agent(s)")


async def router_node(state: ChatState) -> dict:
    run_id = state["run_id"]
    query = state["user_query"]
    history = state.get("chat_history", [])

    history_text = "\n".join(f"{m['role']}: {m['content']}" for m in history[-6:])
    user_prompt = f"Conversation so far:\n{history_text}\n\nUser question: {query}"

    decision = await run_agent(run_id, "router", ROUTER_SYSTEM_PROMPT, user_prompt, RouteDecision)

    if decision is None or not decision.agents:
        return {"route": ["general_qa"], "routing_reasoning": "fallback: routing failed"}

    return {"route": list(dict.fromkeys(decision.agents)), "routing_reasoning": decision.reasoning}
