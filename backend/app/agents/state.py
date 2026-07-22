import operator
from typing import Annotated, TypedDict


class ChatState(TypedDict, total=False):
    paper_id: str
    conversation_id: str
    run_id: str
    user_query: str
    chat_history: list[dict]

    route: list[str]
    routing_reasoning: str

    agent_outputs: Annotated[list[dict], operator.add]
    final_answer: str | None
    final_citations: list[dict]
    final_agents_used: list[str]

    errors: Annotated[list[str], operator.add]
