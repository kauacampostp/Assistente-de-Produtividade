from langchain_core.messages import HumanMessage, SystemMessage

from app import LLM
from graph.state import AgentState


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
