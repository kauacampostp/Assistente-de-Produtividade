"""Constrói e compila o grafo de execução do agente no LangGraph.

Configura os nós de classificação e fluxos especializados (knowledge,
productivity, review e planning), define o roteamento condicional de
intenções e conecta o checkpointer para persistência de memória.
"""

from langgraph.graph import END, START, StateGraph

from graph.nodes import (
    classify_intent,
    knowledge_flow,
    planning_flow,
    productivity_flow,
    review_flow,
    route_intent,
)
from graph.state import AgentState

builder = StateGraph(AgentState)


builder.add_node("classify_intent", classify_intent)
builder.add_node("knowledge", knowledge_flow)
builder.add_node("productivity", productivity_flow)
builder.add_node("review", review_flow)
builder.add_node("planning", planning_flow)


builder.add_edge(START, "classify_intent")


builder.add_conditional_edges(
    "classify_intent",
    route_intent,
    {
        "knowledge": "knowledge",
        "productivity": "productivity",
        "review": "review",
        "planning": "planning",
    },
)


builder.add_edge("knowledge", END)
builder.add_edge("productivity", END)
builder.add_edge("review", END)
builder.add_edge("planning", END)


def build_graph(checkpointer):
    """Compila o grafo com memória persistente."""
    return builder.compile(checkpointer=checkpointer)
