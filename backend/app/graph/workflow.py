from langgraph.graph import END, StateGraph
from langgraph.types import Send

from app.agents.aggregate import aggregate_node
from app.agents.architecture_flowchart import architecture_flowchart_node
from app.agents.general_qa import general_qa_node
from app.agents.math_algorithm import math_algorithm_node
from app.agents.paper_to_code import paper_to_code_node
from app.agents.results_critique import results_critique_node
from app.agents.research_analysis import research_analysis_node
from app.agents.router import router_node
from app.agents.state import ChatState

SPECIALIST_NODES = {
    "research_analysis": research_analysis_node,
    "math_algorithm": math_algorithm_node,
    "results_critique": results_critique_node,
    "paper_to_code": paper_to_code_node,
    "architecture_flowchart": architecture_flowchart_node,
    "general_qa": general_qa_node,
}


def _dispatch(state: ChatState) -> list[Send]:
    route = state.get("route") or ["general_qa"]
    return [Send(agent_key, state) for agent_key in route]


_graph_singleton = None


def get_graph():
    global _graph_singleton
    if _graph_singleton is not None:
        return _graph_singleton

    builder = StateGraph(ChatState)
    builder.add_node("router", router_node)
    for key, node_fn in SPECIALIST_NODES.items():
        builder.add_node(key, node_fn)
    builder.add_node("aggregate", aggregate_node)

    builder.set_entry_point("router")
    builder.add_conditional_edges("router", _dispatch, list(SPECIALIST_NODES.keys()))
    for key in SPECIALIST_NODES:
        builder.add_edge(key, "aggregate")
    builder.add_edge("aggregate", END)

    _graph_singleton = builder.compile()
    return _graph_singleton
