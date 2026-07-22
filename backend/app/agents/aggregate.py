from app.agents.state import ChatState
from app.schemas.chat import AGENT_LABELS


async def aggregate_node(state: ChatState) -> dict:
    outputs = state.get("agent_outputs", [])

    if not outputs:
        return {
            "final_answer": "I couldn't generate a response. Please try again.",
            "final_citations": [],
            "final_agents_used": [],
        }

    if len(outputs) == 1:
        only = outputs[0]
        return {
            "final_answer": only["content"],
            "final_citations": only["citations"],
            "final_agents_used": [only["agent"]],
        }

    sections = []
    all_citations = []
    agents_used = []
    for output in outputs:
        label = AGENT_LABELS.get(output["agent"], output["agent"])
        sections.append(f"## {label}\n\n{output['content']}")
        all_citations.extend(output["citations"])
        agents_used.append(output["agent"])

    return {
        "final_answer": "\n\n".join(sections),
        "final_citations": all_citations,
        "final_agents_used": agents_used,
    }
