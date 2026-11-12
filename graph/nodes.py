from langchain_core.messages import HumanMessage, SystemMessage

from app import LLM
from graph.state import AgentState
from mcp_servers.clients import (
    call_google_calendar_tool,
    call_mcp_tool,
    list_calendar_events,
    local_files_server,
    todoist_server,
)
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


async def knowledge_flow(state: AgentState):
    message = state["user_message"].lower()

    # Se o usuário perguntar quais documentos existem
    if any(
        term in message
        for term in [
            "listar documentos",
            "quais documentos",
            "documentos disponíveis",
        ]
    ):
        result = await call_mcp_tool(
            local_files_server(),
            "listar_documentos",
        )

        documents = "\n".join(item.text for item in result if hasattr(item, "text"))

        response = LLM.invoke(
            [
                SystemMessage(
                    content=("Informe os documentos disponíveis. Não invente nomes.")
                ),
                HumanMessage(content=documents),
            ]
        )

        return {"llm_answer": response.content}

    # Para perguntas sobre conhecimento, mantém o RAG
    result = rag_graph.invoke({"user_message": state["user_message"]})

    return {"llm_answer": result["llm_answer"]}


async def productivity_flow(state: AgentState):
    # Consulta tarefas de hoje e atrasadas
    result = await call_mcp_tool(
        todoist_server(),
        "find-tasks-by-date",
        {
            "startDate": "today",
            "daysCount": 1,
            "overdueOption": "include-overdue",
            "limit": 50,
        },
    )

    # Converte o retorno MCP em texto
    todoist_data = "\n".join(item.text for item in result if hasattr(item, "text"))

    # Gera uma resposta baseada nos dados encontrados
    response = LLM.invoke(
        [
            SystemMessage(
                content="""
            Você é um assistente de produtividade.
            Responda usando exclusivamente os dados do Todoist.
            Organize as tarefas de forma clara.
            Se não houver tarefas, informe isso.
            Não invente tarefas, datas ou prioridades.
            - A consulta considera somente hoje e tarefas atrasadas.
            - Não afirme que não existem tarefas em outros dias.
            - Não tire conclusões sobre informações que não foram consultadas.
            - Diferencie claramente os dados retornados das suas interpretações.
        """
            ),
            HumanMessage(
                content=f"""
            Pergunta do usuário: {state["user_message"]}

            Dados retornados pelo Todoist:
            {todoist_data}
        """
            ),
        ]
    )

    return {
        "todoist_result": todoist_data,
        "llm_answer": response.content,
    }


def review_flow(state: AgentState):
    return {"llm_answer": "Fluxo de revisão da rotina ainda não implementado."}


async def planning_flow(state: AgentState):
    events = list_calendar_events()

    calendar_data = "\n".join(
        f"""
        Evento: {event.get("summary", "Sem título")}
        Início: {event.get("start", {}).get("dateTime", event.get("start", {}).get("date", "Não informado"))}
        Fim: {event.get("end", {}).get("dateTime", event.get("end", {}).get("date", "Não informado"))}
        Local: {event.get("location", "Não informado")}
        """
        for event in events
    )

    response = LLM.invoke(
        [
            SystemMessage(
                content="""
            Você é um assistente de planejamento pessoal.
            Organize os compromissos cronologicamente.
            Informe título, data, horário e local quando disponíveis.
            Não invente informações.
            Se não houver eventos, informe isso.
        """
            ),
            HumanMessage(
                content=f"""
            Pergunta: {state["user_message"]}

            Eventos encontrados:
            {calendar_data or "Nenhum compromisso futuro encontrado."}
        """
            ),
        ]
    )

    return {"calendar_events": [], "llm_answer": response.content}
