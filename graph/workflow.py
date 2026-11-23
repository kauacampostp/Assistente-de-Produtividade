from langgraph.graph import END, START, StateGraph

from graph.nodes import (
    classify_intent,
    knowledge_flow,
    planning_flow,
    productivity_flow,
    review_flow,
    route_after_input_validation,
    route_intent,
    validate_input_node,
    validate_output_node,
)
from graph.state import AgentState

builder = StateGraph(AgentState)

# Nós de segurança
builder.add_node("validate_input", validate_input_node)
builder.add_node("validate_output", validate_output_node)

# Nós principais
builder.add_node("classify_intent", classify_intent)
builder.add_node("knowledge", knowledge_flow)
builder.add_node("productivity", productivity_flow)
builder.add_node("review", review_flow)
builder.add_node("planning", planning_flow)

# Entrada: validação antes do processamento
builder.add_edge(START, "validate_input")

builder.add_conditional_edges(
    "validate_input",
    route_after_input_validation,
    {
        "blocked": "validate_output",
        "continue": "classify_intent",
    },
)

# Roteamento por intenção
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

# Todas as respostas passam pela validação de saída
builder.add_edge("knowledge", "validate_output")
builder.add_edge("productivity", "validate_output")
builder.add_edge("review", "validate_output")
builder.add_edge("planning", "validate_output")

builder.add_edge("validate_output", END)


def build_graph(checkpointer):
    return builder.compile(checkpointer=checkpointer)
