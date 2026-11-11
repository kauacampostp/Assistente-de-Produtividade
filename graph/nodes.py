from langchain_core.messages import HumanMessage, SystemMessage

from app import LLM
from graph.state import AgentState
from rag.workflow import rag_graph


# função para classificar a intenção do usuário
def classify_intent(state: AgentState):

    SYSTEM_PROMPT = """
    Classifique a mensagem em uma categoria:
    - knowledge
    - productivity
    - review
    - planning

    Retorne somente o nome da categoria.
    """

    response = LLM.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=state["user_message"]),
        ]
    )

    intent = response.content.strip().lower()

    return {"intent": intent}


# função para guiar rota a parti da intenção detectada
def route_intent(state: AgentState):
    intent = state["intent"]

    routes = {
        "knowledge": "knowledge",
        "productivity": "productivity",
        "review": "review",
        "planning": "planning",
    }

    if intent not in routes:
        raise ValueError(f"Intenção inválida: {intent}")

    return routes[intent]


def knowledge_flow(state: AgentState):
    result = rag_graph.invoke({"user_message": state["user_message"]})

    return {"llm_answer": result["llm_answer"]}


def productivity_flow(state: AgentState):
    return {"llm_answer": "Fluxo de produtividade ainda não implementado."}


def review_flow(state: AgentState):
    return {"llm_answer": "Fluxo de revisão da rotina ainda não implementado."}


def planning_flow(state: AgentState):
    return {"llm_answer": "Fluxo de planejamento ainda não implementado."}
