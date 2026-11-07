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

# Cria o construtor do grafo
builder = StateGraph(AgentState)

# Registra os nós
builder.add_node("classify_intent", classify_intent)
builder.add_node("knowledge", knowledge_flow)
builder.add_node("productivity", productivity_flow)
builder.add_node("review", review_flow)
builder.add_node("planning", planning_flow)


# Define o início do fluxo
builder.add_edge(START, "classify_intent")


# Define o roteamento condicional
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


# Todos os caminhos terminam após executar seu respectivo nó
builder.add_edge("knowledge", END)
builder.add_edge("productivity", END)
builder.add_edge("review", END)
builder.add_edge("planning", END)


# Compila o grafo
graph = builder.compile()
