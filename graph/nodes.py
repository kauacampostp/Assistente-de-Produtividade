import json

from langchain_core.messages import HumanMessage, SystemMessage

from app import LLM
from graph.state import AgentState
from mcp_servers.clients import (
    call_mcp_tool,
    call_todoist_tool,
    list_calendar_events,
    local_files_server,
)
from rag.workflow import rag_graph
from skills.loader import get_skill_catalog, load_skill


def get_conversation_context(state: AgentState) -> str:
    """Formata o histórico da conversa para enviar ao LLM."""

    history = state.get("conversation_history", [])

    if not history:
        return "Nenhuma conversa anterior."

    return "\n".join(
        f"Usuário: {item['user']}\nAssistente: {item['assistant']}"
        for item in history[-10:]
    )


def select_skill(message: str, history: str = ""):
    """Seleciona e carrega uma Skill conforme a mensagem do usuário."""

    catalog = get_skill_catalog()

    if not catalog:
        return None, None

    descriptions = "\n".join(
        f"- Nome: {skill['name']}\n  Descrição: {skill['description']}"
        for skill in catalog
    )

    response = LLM.invoke(
        [
            SystemMessage(
                content=f"""
            Você seleciona Skills para um assistente pessoal.

            Analise a mensagem e escolha a Skill mais adequada
            entre as opções disponíveis.

            Se nenhuma Skill for necessária, responda somente: none.

            Responda exclusivamente com o nome exato da Skill
            ou com none.

            Skills disponíveis:
            {descriptions}
            Histórico da conversa:
            {history}
        """
            ),
            HumanMessage(content=message),
        ]
    )

    selected = response.content.strip().strip("`")

    if selected.lower() == "none":
        return None, None

    available_names = {skill["name"] for skill in catalog}

    if selected not in available_names:
        return None, None

    return selected, load_skill(selected)


# CLASSIFICAÇÃO


def classify_intent(state: AgentState):
    # Confirmações retornam diretamente à produtividade
    if state.get("pending_operation"):
        return {"intent": "productivity"}

    message = state["user_message"].lower().strip()

    todoist_keywords = [
        "todoist",
        "tarefa",
        "tarefas",
        "projeto",
        "projetos",
        "lista de tarefas",
        "minhas tarefas",
        "meus projetos",
        "crie uma tarefa",
        "criar tarefa",
        "adicione uma tarefa",
        "adicionar tarefa",
        "atualize a tarefa",
        "atualizar tarefa",
    ]

    if any(keyword in message for keyword in todoist_keywords):
        intent = "productivity"
    else:
        system_prompt = """
        Classifique a mensagem em uma categoria:

        - knowledge: perguntas sobre documentos e conhecimentos armazenados.
        - productivity: consultas ou operações relacionadas a tarefas.
        - review: revisão da rotina e produtividade.
        - planning: planejamento e compromissos do calendário.

        Retorne somente o nome da categoria.
        """

        response = LLM.invoke(
            [
                SystemMessage(
                    content=f"""
                    {system_prompt}

                    Histórico da conversa:
                    {get_conversation_context(state)}
                    """
                ),
                HumanMessage(content=state["user_message"]),
            ]
        )

        intent = response.content.strip().lower()

        if intent not in {"knowledge", "productivity", "review", "planning"}:
            intent = "productivity"

    # Seleciona e carrega a Skill
    skill_name, skill_content = select_skill(
        state["user_message"], get_conversation_context(state)
    )

    return {
        "intent": intent,
        "skill_name": skill_name,
        "skill_content": skill_content,
    }


def route_intent(state: AgentState):
    return state["intent"]


# CONHECIMENTO
async def knowledge_flow(state: AgentState):
    message = state["user_message"].lower()

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
                    content="Informe os documentos disponíveis. Não invente nomes."
                ),
                HumanMessage(content=documents),
            ]
        )

        return {"llm_answer": response.content}

    result = await rag_graph.ainvoke(
        {
            "user_message": state["user_message"],
            "conversation_history": state.get("conversation_history", []),
        }
    )

    answer = result["llm_answer"]
    skill_content = state.get("skill_content")

    if skill_content:
        response = LLM.invoke(
            [
                SystemMessage(
                    content=f"""
                Você deve revisar a resposta do assistente seguindo
                as instruções desta Skill:

                {skill_content}

                Preserve a fidelidade aos documentos recuperados.
                Não acrescente informações sem fundamento nas fontes.
            """
                ),
                HumanMessage(
                    content=f"""
                Pergunta do usuário:
                {state["user_message"]}

                Resposta produzida pelo RAG:
                {answer}
            """
                ),
            ]
        )

        answer = response.content

    return {
        "llm_answer": answer,
        "skill_name": state.get("skill_name"),
    }


# AUXILIAR: CONVERTER RETORNO MCP EM TEXTO
def mcp_result_to_text(result):
    texts = [item.text for item in result if hasattr(item, "text")]

    return "\n".join(texts) if texts else str(result)


# AUXILIAR: INTERPRETAR A OPERAÇÃO SOLICITADA
def extract_operation(
    message: str, skill_content: str | None = None, history: str = ""
):
    prompt = """
    Você é um interpretador de operações do Todoist.

    Identifique uma única operação solicitada pelo usuário.

    Operações permitidas:
    - find-tasks
    - add-tasks
    - update-tasks
    - find-projects
    - add-projects
    - update-projects

    Retorne SOMENTE um JSON válido neste formato:
    {
        "tool": "nome-da-ferramenta",
        "arguments": {},
        "summary": "descrição da operação"
    }

    Regras:
    - Para consultar ou pesquisar tarefas, use find-tasks.
    - Para consultar ou pesquisar projetos, use find-projects.
    - Para criar tarefas, cada item dentro de "tasks" DEVE utilizar "content" como nome da tarefa.
    - Nunca utilize "name" para tarefas.
    - Exemplo correto:
        {
            "tasks": [
                {
                    "content": "Estudar Python",
                    "priority": "p2"
                }
            ]
        }

    - Para atualizar tarefas, utilize "id" para identificar a tarefa e "content" para alterar seu nome.
    - Para criar projetos, use add-projects com {"projects": [...]}.
    - Para atualizar projetos, use update-projects com {"projects": [...]}.
    - Para criar projetos, utilize "name" como nome do projeto.
    - Não confunda a estrutura de tarefas com a de projetos.
    - Prioridade de tarefas deve ser p1, p2, p3 ou p4.
    - Para atualizar tarefas, use update-tasks.
    - Para atualizar projetos, use update-projects.
    - Se o usuário informar o nome de um projeto, mas não seu ID, retorne o nome no campo "name" para que o sistema possa pesquisar o projeto e obter o ID.
    - Nunca invente IDs.
    - Para atualizar um projeto como favorito, use "isFavorite": true.
    - Para atualizar um projeto como não favorito, use "isFavorite": false.
    - Se faltarem informações obrigatórias, não invente valores.
    - Não interprete uma consulta como autorização para alterar dados.
    - Se houver instruções de uma Skill, utilize-as para interpretar a solicitação, respeitando as ferramentas permitidas.
    """

    response = LLM.invoke(
        [
            SystemMessage(
                content=f"""
                    {prompt}

                    Instruções da Skill selecionada:
                    {skill_content or "Nenhuma Skill selecionada."}
                    Histórico da conversa:
                    {history}
                """
            ),
            HumanMessage(content=message),
        ]
    )

    raw = response.content.strip()

    # Remove cercas Markdown, caso o modelo as retorne
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0]

    start = raw.find("{")
    end = raw.rfind("}") + 1

    if start < 0 or end <= start:
        raise ValueError("O modelo não retornou um JSON válido.")

    return json.loads(raw[start:end])


# PRODUTIVIDADE
async def productivity_flow(state: AgentState):
    message = state["user_message"].strip().lower()

    pending = state.get("pending_operation")

    # 1. TRATAR CONFIRMAÇÃO OU CANCELAMENTO

    if pending:
        if message in {"sim", "s", "confirmo", "confirmar", "pode", "pode executar"}:
            result = await call_todoist_tool(
                pending["tool"],
                pending["arguments"],
            )

            result_text = mcp_result_to_text(result)

            return {
                "pending_operation": None,
                "todoist_result": result_text,
                "llm_answer": (
                    f"Resultado da operação: {pending['summary']}\n\n{result_text}"
                ),
            }

        if message in {"não", "nao", "n", "cancelar", "cancela"}:
            return {
                "pending_operation": None,
                "llm_answer": "Operação cancelada. Nenhuma alteração foi realizada no Todoist.",
            }

        return {
            "llm_answer": (
                f"Você ainda tem uma operação aguardando confirmação:\n"
                f"{pending['summary']}\n\n"
                "Responda 'sim' para executar ou 'não' para cancelar."
            )
        }

    # 2. IDENTIFICAR A OPERAÇÃO

    try:
        operation = extract_operation(
            state["user_message"],
            state.get("skill_content"),
            get_conversation_context(state),
        )

        tool_name = operation["tool"]
        arguments = operation["arguments"]
        summary = operation.get("summary", "Operação no Todoist")

    except Exception as error:
        return {"llm_answer": f"Não consegui interpretar sua solicitação: {error}"}

    allowed_tools = {
        "find-tasks",
        "add-tasks",
        "update-tasks",
        "find-projects",
        "add-projects",
        "update-projects",
    }

    if tool_name not in allowed_tools or not isinstance(arguments, dict):
        return {
            "llm_answer": "Não consegui identificar uma operação válida do Todoist."
        }

    # 3. CONSULTAS: EXECUÇÃO IMEDIATA

    if tool_name in {"find-tasks", "find-projects"}:
        result = await call_todoist_tool(tool_name, arguments)
        result_text = mcp_result_to_text(result)

        response = LLM.invoke(
            [
                SystemMessage(
                    content=f"""
                    Responda usando exclusivamente os dados retornados pelo Todoist.
                    Não invente tarefas, projetos, IDs ou datas.
                    Organize as informações de maneira clara.
                    
                    Instruções adicionais da Skill:
                    {state.get("skill_content") or "Nenhuma Skill selecionada."}
                    Histórico da conversa:
                    {get_conversation_context(state)}
                """
                ),
                HumanMessage(
                    content=f"""
                Pergunta: {state["user_message"]}

                Resultado do Todoist:
                {result_text}
            """
                ),
            ]
        )

        return {
            "todoist_result": result_text,
            "llm_answer": response.content,
        }

    # 4. CADASTROS E ATUALIZAÇÕES: PEDIR CONFIRMAÇÃO

    required_keys = {
        "add-tasks": "tasks",
        "update-tasks": "tasks",
        "add-projects": "projects",
        "update-projects": "projects",
    }

    key = required_keys[tool_name]
    items = arguments.get(key)
    # Corrige o campo obrigatório de criação de tarefas
    if tool_name == "add-tasks":
        for item in items:
            if "name" in item and "content" not in item:
                item["content"] = item.pop("name")

            if not item.get("content"):
                return {
                    "llm_answer": (
                        "Não foi possível criar a tarefa: "
                        "o conteúdo da tarefa não foi informado."
                    )
                }

    if not isinstance(items, list) or not items:
        return {
            "llm_answer": (
                f"Não encontrei os dados necessários para {summary}. "
                "Informe os detalhes que faltam."
            )
        }

    if tool_name == "update-projects":
        for item in items:
            if not item.get("id") and item.get("name"):
                result = await call_todoist_tool(
                    "find-projects",
                    {"searchText": item["name"], "limit": 10},
                )

                result_text = mcp_result_to_text(result)

                response = LLM.invoke(
                    [
                        SystemMessage(
                            content="""
                        Encontre o ID do projeto solicitado nos dados fornecidos.
                        Retorne somente JSON: {"id": "ID_ENCONTRADO"}.
                        Use exclusivamente os dados recebidos.
                        Se não encontrar correspondência exata, retorne {"id": null}.
                    """
                        ),
                        HumanMessage(
                            content=f"""
                        Projeto procurado: {item["name"]}
                        Projetos encontrados:
                        {result_text}
                    """
                        ),
                    ]
                )

                try:
                    data = json.loads(response.content)
                    item["id"] = data.get("id")
                except (json.JSONDecodeError, AttributeError):
                    item["id"] = None

    if tool_name in {"update-tasks", "update-projects"} and not all(
        isinstance(item, dict) and item.get("id") for item in items
    ):
        return {"llm_answer": "Não encontrei o ID do item. Verifique o nome informado."}

    return {
        "pending_operation": {
            "tool": tool_name,
            "arguments": arguments,
            "summary": summary,
        },
        "llm_answer": (
            f"Operação preparada: {summary}\n\n"
            f"Dados: {json.dumps(arguments, ensure_ascii=False, indent=2)}\n\n"
            "Deseja executar essa operação no Todoist? "
            "Responda 'sim' para confirmar ou 'não' para cancelar."
        ),
    }


# REVISÃO
async def review_flow(state: AgentState):
    # Consultar tarefas do Todoist
    tasks_result = await call_todoist_tool(
        "find-tasks",
        {"limit": 20},
    )
    tasks_data = mcp_result_to_text(tasks_result)

    # Limitar dados das tarefas
    tasks_data = tasks_data[:5000]

    # Consultar compromissos do calendário
    events = list_calendar_events()

    calendar_data = "\n".join(
        f"""
        Evento: {event.get("summary", "Sem título")}
        Início: {event.get("start", {}).get("dateTime", event.get("start", {}).get("date", "Não informado"))}
        Fim: {event.get("end", {}).get("dateTime", event.get("end", {}).get("date", "Não informado"))}
        """
        for event in events[:8]
    )

    # Limitar histórico da conversa
    history = get_conversation_context(state)[-1500:]

    response = LLM.invoke(
        [
            SystemMessage(
                content=f"""
                Você é um assistente especializado em revisão de rotina.

                Analise tarefas e compromissos.
                Identifique:
                - Tarefas pendentes e prioridades.
                - Compromissos próximos.
                - Possíveis conflitos.
                - Sobrecarga ou concentração de atividades.
                - Recomendações para organizar a rotina.

                Não invente informações.
                Não afirme que uma tarefa está atrasada sem evidência.
                Não altere tarefas ou compromissos.

                Histórico recente:
                {history}
            """
            ),
            HumanMessage(
                content=f"""
                Solicitação: {state["user_message"]}

                Tarefas do Todoist:
                {tasks_data}

                Compromissos do Google Calendar:
                {calendar_data or "Nenhum compromisso encontrado."}
            """
            ),
        ]
    )

    return {
        "todoist_result": tasks_data,
        "calendar_events": events,
        "llm_answer": response.content,
    }


# PLANEJAMENTO
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
                content=f"""
                Você é um assistente de planejamento pessoal.

                Organize os compromissos cronologicamente.
                Informe título, data, horário e local quando disponíveis.
                Não invente informações.
                Se não houver eventos, informe isso.

                Histórico da conversa:
                {get_conversation_context(state)}
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

    return {
        "calendar_events": events,
        "llm_answer": response.content,
    }
