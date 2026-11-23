"""Define os esquemas de estado compartilhado e tipos de dados do agente.

Contém as estruturas TypedDict utilizadas pelo LangGraph para trafegar
mensagens, histórico conversacional, documentos recuperados (RAG),
tarefas do Todoist e eventos de calendário entre os nós do fluxo.
"""

from typing import Literal, NotRequired, TypedDict

from langchain_core.documents import Document

Intent = Literal["knowledge", "productivity", "review", "planning"]


class Task(TypedDict):
    """Representa uma tarefa do Todoist."""

    title: str
    priority: int
    due_date: str


class CalendarEvents(TypedDict):
    """Representa um evento do calendário."""

    title: str
    start: str
    end: str


class AgentState(TypedDict):
    """Define molde com as variáveis necessárias para a execução do agente."""

    # Mensagem do usuário e intenção da mensagem
    user_message: str
    intent: NotRequired[Intent]

    # Memória conversacional
    conversation_history: NotRequired[list[dict[str, str]]]

    # RAG
    find_docs: NotRequired[list[str]]

    # RAG agêntico
    search_query: NotRequired[str]
    retrieved_docs: NotRequired[list[Document]]
    attempts: NotRequired[int]
    documents_relevant: NotRequired[bool]

    # MCP (Ferramentas externas: Todoist e Calendar)
    todoist_tasks: NotRequired[list[Task]]
    todoist_result: NotRequired[str]
    calendar_events: NotRequired[list[CalendarEvents]]

    # Skills (acompanhamento_projetos e analise_documental)
    skill_name: NotRequired[str | None]
    skill_content: NotRequired[str | None]

    # Guardrails
    guardrail_error: NotRequired[str | None]
    
    # Resposta
    llm_answer: NotRequired[str]

    # Operação aguardando confirmação
    pending_operation: NotRequired[dict | None]
