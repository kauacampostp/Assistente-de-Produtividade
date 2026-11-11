
from langgraph.graph import StateGraph, START, END

from graph.state import AgentState

from rag.nodes import (
    retrieve,
    grade_documents,
    rewrite_query,
    generate_answer,
    no_context,
)


MAX_ATTEMPTS = 2

builder = StateGraph(AgentState)

# Registra os nós
builder.add_node("retrieve", retrieve)
builder.add_node("grade_documents", grade_documents)
builder.add_node("rewrite_query", rewrite_query)
builder.add_node("generate_answer", generate_answer)
builder.add_node("no_context", no_context)

# Fluxo principal
builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "grade_documents")


# Decide o próximo passo
def route_after_grading(state: AgentState):
    if state["documents_relevant"]:
        return "generate_answer"

    if state.get("attempts", 0) < MAX_ATTEMPTS:
        return "rewrite_query"

    return "no_context"


builder.add_conditional_edges(
    "grade_documents",
    route_after_grading,
    {
        "generate_answer": "generate_answer",
        "rewrite_query": "rewrite_query",
        "no_context": "no_context",
    },
)

# Depois de reformular, pesquisa novamente
builder.add_edge("rewrite_query", "retrieve")

# Fim dos caminhos
builder.add_edge("generate_answer", END)
builder.add_edge("no_context", END)

rag_graph = builder.compile()
