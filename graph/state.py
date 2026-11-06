# permite definir a estrutura e tipo da chave de um dic
from typing import Literal, NotRequired, TypedDict

Intent = Literal["knowledge", "productivity", "review", "planning"]


# Criamos classes auxiliares para tratarmos melhor das informações
class Task(TypedDict):
    title: str
    priority: int
    due_date: str


class CalendarEvents(TypedDict):
    title: str
    start: str
    end: str


# Classe principal que vai guarda a informaçẽos para o proximos nós (State)
class AgentState(TypedDict):
    user_message: str
    intent: NotRequired[Intent]

    # RAG
    find_docs: NotRequired[list[str]]

    # MCP
    todoist_tasks: NotRequired[list[Task]]
    calendar_events: NotRequired[list[CalendarEvents]]

    # Resposta
    llm_answer: NotRequired[str]
