import json
import re

from langchain_core.messages import HumanMessage, SystemMessage
from mcp import ClientSession
from mcp.client.stdio import stdio_client

from app import LLM
from graph.state import AgentState
from guardrails.input import validate_input
from guardrails.output import validate_output
from mcp_servers.clients import (
    call_todoist_tool,
    list_calendar_events,
    local_files_server,
)
from rag.workflow import rag_graph
from skills.loader import get_skill_catalog, load_skill


def get_conversation_context(state):
    history = state.get("conversation_history", [])

    if not history:
        return "Nenhuma conversa anterior."

    return "\n".join(
        f"Usuário: {item['user']}\nAssistente: {item['assistant'][:600]}"
        for item in history[-4:]
    )


# GUARDRAILS


def validate_input_node(state: AgentState):
    valid, error = validate_input(state["user_message"])
    return {
        "guardrail_error": None if valid else error,
        "tools_used": [],
        "skill_name": None,
        "skill_content": None,
    }

def route_after_input_validation(state: AgentState):
    """Decide se a mensagem pode continuar."""

    if state.get("guardrail_error"):
        return "blocked"

    return "continue"


def validate_output_node(state: AgentState):
    """Valida a resposta antes de entregá-la ao usuário."""

    if state.get("guardrail_error"):
        answer = state["guardrail_error"]
    else:
        answer = state.get("llm_answer", "")

    return {
        "llm_answer": validate_output(answer),
    }


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

    local_file_keywords = [
        "arquivos locais",
        "arquivo local",
        "diretório de notas",
        "nota de resumo",
        "criar uma nota",
        "crie uma nota",
        "listar documentos",
        "quais documentos",
        "documentos disponíveis",
        "meus documentos",
        "tokenizadores",
        "transformers",
        "embeddings",
        "rag",
        "microsserviços",
        "deep work",
        "análise documental",
        ".md",
    ]

    review_keywords = [
        "sobrecarregado",
        "revise minha rotina",
        "revisão da rotina",
        "revisar rotina",
        "cruze meus compromissos",
        "tarefas atrasadas",
    ]

    calendar_keywords = [
        "google calendar",
        "calendário",
        "agenda",
        "compromisso",
        "compromissos",
    ]

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

    has_todoist = any(k in message for k in todoist_keywords)
    has_calendar = any(k in message for k in calendar_keywords)
    has_review = any(k in message for k in review_keywords)
    has_local_files = any(k in message for k in local_file_keywords)

    # Prioridade 1: Revisão de rotina ou consultas cruzadas (Todoist + Calendar)
    if has_review or (has_todoist and has_calendar):
        intent = "review"
    # Prioridade 2: Arquivos locais e base de documentos (MCP local_files / RAG)
    elif has_local_files and not has_todoist:
        intent = "knowledge"
    # Prioridade 3: Operações específicas de tarefas/projetos no Todoist
    elif has_todoist:
        intent = "productivity"
    else:
        system_prompt = """
        Classifique a mensagem em uma categoria:

        - knowledge: perguntas sobre documentos, arquivos locais, anotações e conhecimentos armazenados.
        - productivity: consultas ou operações relacionadas exclusivamente a tarefas e projetos no Todoist.
        - review: revisão da rotina, sobrecarga ou consultas combinando tarefas e agenda.
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


# AUXILIAR: EXECUÇÃO DINÂMICA NO SERVIDOR MCP LOCAL_FILES
async def execute_local_files_mcp(user_message: str):
    """Executa as ferramentas do MCP local_files de forma determinística.

    O código decide quais ferramentas chamar; o LLM só redige o conteúdo da nota.
    """
    server_params = local_files_server()
    msg = user_message.lower()

    wants_create = bool(
        re.search(r"\b(crie|criar|cria|salve|salvar)\b", msg)
        and re.search(r"(\bnota\b|\barquivo\b|\.md\b|\.txt\b)", msg)
    )

    # Nome do arquivo entre aspas, ex.: 'checklist_revisao.md'
    name_match = re.search(r"['\"“‘]([\w\-. /]+\.(?:md|txt))['\"”’]", user_message)
    filename = name_match.group(1) if name_match else "nota_resumo.md"

    outputs: list[str] = []
    used: list[str] = []

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # 1. Sempre lista (também serve de base para o conteúdo da nota)
                res = await session.call_tool("listar_documentos", {})
                listing = mcp_result_to_text(getattr(res, "content", res))
                outputs.append(f"[listar_documentos]\n{listing}")
                used.append("local_files:listar_documentos")

                # 2. Cria a nota, se foi pedido
                if wants_create:
                    note = LLM.invoke(
                        [
                            SystemMessage(
                                content=(
                                    "Escreva em Markdown, em português, uma nota de "
                                    "resumo/checklist de revisão baseada SOMENTE na "
                                    "lista de arquivos fornecida. Não invente arquivos. "
                                    "Não chame ferramentas. Responda apenas com o "
                                    "conteúdo da nota."
                                )
                            ),
                            HumanMessage(
                                content=(
                                    f"Pedido do usuário: {user_message}\n\n"
                                    f"Arquivos disponíveis:\n{listing}"
                                )
                            ),
                        ]
                    )

                    res = await session.call_tool(
                        "criar_nota",
                        {"relative_path": filename, "content": note.content},
                    )
                    created = mcp_result_to_text(getattr(res, "content", res))

                    if getattr(res, "isError", False):
                        outputs.append(f"[criar_nota] ERRO: {created}")
                    else:
                        outputs.append(f"[criar_nota]\n{created}")
                        used.append("local_files:criar_nota")

    except Exception as error:
        outputs.append(f"[erro no servidor MCP local_files] {error}")

    return "\n\n".join(outputs), used


def is_file_operation(message: str) -> bool:
    """Detecta pedidos para listar ou criar arquivos locais."""
    m = message.lower()

    create = re.search(r"\b(crie|criar|cria|salve|salvar)\b", m) and re.search(
        r"(\bnota\b|\barquivo\b|\.md\b|\.txt\b)", m
    )
    listing = re.search(r"\b(list\w*|quais)\b", m) and re.search(
        r"\b(arquivos|documentos|notas)\b", m
    )

    return bool(create or listing)


# CONHECIMENTO
async def knowledge_flow(state: AgentState):
    message = state["user_message"].lower()

    if is_file_operation(state["user_message"]):
        mcp_output, tools_used = await execute_local_files_mcp(state["user_message"])

        response = LLM.invoke(
            [
                SystemMessage(
                    content=(
                        "Informe os resultados obtidos pelo servidor MCP de arquivos locais. "
                        "Não invente nomes de arquivos ou conteúdos. "
                        "IMPORTANTE: Não chame ferramentas."
                    )
                ),
                HumanMessage(
                    content=f"Solicitação: {state['user_message']}\n\nRetorno do MCP local_files:\n{mcp_output}"
                ),
            ]
        )

        return {
            "llm_answer": response.content,
            "skill_name": None,
            "tools_used": tools_used,
        }

    result = await rag_graph.ainvoke(
        {
            "user_message": state["user_message"],
            "conversation_history": state.get("conversation_history", []),
        }
    )

    answer = result.get("llm_answer", "")
    docs = result.get("retrieved_docs", [])
    retrieved_context = "\n\n".join(
        f"Fonte: {d.metadata.get('source', 'desconhecida')}\n{d.page_content}"
        for d in docs
    )
    tools_used = ["rag:chromadb"] if result.get("attempts", 0) > 0 else []
    skill_content = state.get("skill_content")

    if skill_content and result.get("documents_relevant"):
        response = LLM.invoke(
            [
                SystemMessage(
                    content=f"""
                Você está operando sobre a base de conhecimento local do usuário (ChromaDB/RAG).
                Os dados e arquivos apresentados abaixo JÁ FORAM recuperados e verificados na base real do usuário.
                NUNCA diga que não tem acesso aos documentos nem que não pode confirmar a existência dos arquivos citados abaixo.

                Estruture e aprofunde a resposta seguindo as diretrizes desta Skill:
                {skill_content}

                Preserve total fidelidade aos documentos recuperados, cite os nomes dos arquivos de origem e não invente informações.
                IMPORTANTE: Não chame ou invoque nenhuma ferramenta. Apenas redija a resposta final em texto.
            """
                ),
                HumanMessage(
                    content=f"""
                Pergunta do usuário:
                {state["user_message"]}

                Resposta inicial do RAG:
                {answer}

                Trechos / Contexto recuperado:
                {retrieved_context}
            """
                ),
            ]
        )

        if response.content and response.content.strip():
            answer = response.content

    return {
        "llm_answer": answer,
        "skill_name": state.get("skill_name")
        if skill_content and result.get("documents_relevant")
        else None,
        "tools_used": tools_used,
    }


# AUXILIAR: CONVERTER RETORNO MCP EM TEXTO
def mcp_result_to_text(result):
    texts = [item.text for item in result if hasattr(item, "text")]

    return "\n".join(texts) if texts else str(result)


def validate_operation_arguments(tool_name: str, arguments: dict):
    """Valida os argumentos antes de executar uma ferramenta."""

    if not isinstance(arguments, dict):
        return False, "Os argumentos precisam ser um objeto."

    required_keys = {
        "add-tasks": "tasks",
        "update-tasks": "tasks",
        "add-projects": "projects",
        "update-projects": "projects",
    }

    if tool_name in required_keys:
        key = required_keys[tool_name]
        items = arguments.get(key)

        if not isinstance(items, list) or not items:
            return False, f"O campo '{key}' precisa conter uma lista."

        if not all(isinstance(item, dict) for item in items):
            return False, "Todos os itens precisam ser objetos válidos."

        for item in items:
            if tool_name == "add-tasks":
                if (
                    not isinstance(item.get("content"), str)
                    or not item["content"].strip()
                ):
                    return False, "Toda tarefa precisa ter um conteúdo válido."

                if item.get("priority") is not None and item["priority"] not in (
                    "p1",
                    "p2",
                    "p3",
                    "p4",
                    1,
                    2,
                    3,
                    4,
                ):
                    return False, "Prioridade de tarefa inválida."

            elif tool_name == "update-tasks":
                if not item.get("id"):
                    return False, "Toda tarefa a atualizar precisa de um ID."

            elif tool_name == "add-projects":
                if not isinstance(item.get("name"), str) or not item["name"].strip():
                    return False, "Todo projeto precisa de um nome válido."

            elif tool_name == "update-projects":
                if not item.get("id"):
                    return False, "Todo projeto a atualizar precisa de um ID."

    return True, None


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

    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0]

    start = raw.find("{")
    end = raw.rfind("}") + 1

    if start < 0 or end <= start:
        raise ValueError(
            "Operação bloqueada: não é possível executar ações não permitidas ou sem confirmação explícita."
        )

    return json.loads(raw[start:end])


# PRODUTIVIDADE
async def productivity_flow(state: AgentState):
    message = state["user_message"].strip().lower()

    pending = state.get("pending_operation")

    # 1. TRATAR CONFIRMAÇÃO OU CANCELAMENTO

    if pending:
        if message in {"sim", "s", "confirmo", "confirmar", "pode", "pode executar"}:
            allowed_tools = {
                "add-tasks",
                "update-tasks",
                "add-projects",
                "update-projects",
            }

            tool_name = pending.get("tool")
            arguments = pending.get("arguments")

            if tool_name not in allowed_tools:
                return {
                    "pending_operation": None,
                    "llm_answer": "Operação bloqueada: ferramenta não autorizada.",
                }

            valid, error = validate_operation_arguments(tool_name, arguments)

            if not valid:
                return {
                    "pending_operation": None,
                    "llm_answer": f"Operação bloqueada: {error}",
                }

            try:
                result = await call_todoist_tool(
                    tool_name,
                    arguments,
                )

                result_text = mcp_result_to_text(result)

                if getattr(result, "isError", False):
                    return {
                        "pending_operation": None,
                        "todoist_result": result_text,
                        "llm_answer": (
                            "A operação não foi concluída pelo Todoist.\n\n"
                            f"Detalhes: {result_text}"
                        ),
                    }

                return {
                    "pending_operation": None,
                    "todoist_result": result_text,
                    "tools_used": [f"todoist:{tool_name}"],
                    "llm_answer": (
                        f"Operação enviada ao Todoist: {pending['summary']}\n\n"
                        f"Retorno da ferramenta:\n{result_text}"
                    ),
                }

            except Exception as error:
                return {
                    "pending_operation": None,
                    "llm_answer": (
                        "Não foi possível executar a operação no Todoist. "
                        f"Erro: {str(error)}"
                    ),
                }

        if message in {"não", "nao", "n", "cancelar", "cancela"}:
            return {
                "pending_operation": None,
                "llm_answer": "Operação cancelada. Nenhuma alteração foi solicitada.",
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
        if any(p in message for p in ["projeto", "projetos", "acompanhamento"]):
            tool_name = "find-projects"
            arguments = {"limit": 20}
        else:
            tool_name = "find-tasks"
            arguments = {"limit": 20}

    if tool_name in {
        "add-tasks",
        "update-tasks",
        "add-projects",
        "update-projects",
    }:
        key = {
            "add-tasks": "tasks",
            "update-tasks": "tasks",
            "add-projects": "projects",
            "update-projects": "projects",
        }[tool_name]

        items = arguments.get(key)

        if not isinstance(items, list) or not items:
            return {"llm_answer": "Operação inválida: faltam os dados necessários."}

        if not all(isinstance(item, dict) for item in items):
            return {
                "llm_answer": "Operação inválida: existem itens com formato incorreto."
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
                    IMPORTANTE: Não chame ou invoque nenhuma ferramenta. Todos os dados necessários já foram coletados. Apenas responda ao usuário em texto.
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
            "tools_used": [f"todoist:{tool_name}"],
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
    lookup_tools: list[str] = []
    if tool_name == "update-projects":
        for item in items:
            if not item.get("id") and item.get("name"):
                result = await call_todoist_tool(
                    "find-projects",
                    {"searchText": item["name"], "limit": 10},
                )
                lookup_tools.append("todoist:find-projects")

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
        "tools_used": lookup_tools,
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

    # Se a solicitação mencionar anotações/documentos, consulta também o RAG
    rag_notes = ""
    msg_lower = state["user_message"].lower()
    if any(
        term in msg_lower
        for term in [
            "anotações",
            "notas",
            "documentos",
            "deep work",
            "produtividade",
            "arquitetura",
            "llm",
        ]
    ):
        rag_res = await rag_graph.ainvoke(
            {
                "user_message": state["user_message"],
                "conversation_history": state.get("conversation_history", []),
            }
        )
        rag_notes = rag_res.get("llm_answer", "")

    history = get_conversation_context(state)[-1500:]

    response = LLM.invoke(
        [
            SystemMessage(
                content=f"""
                Você é um assistente especializado em revisão de rotina e planejamento.

                Analise tarefas, compromissos e (quando fornecidas) anotações do usuário.
                Identifique:
                - Tarefas pendentes e prioridades.
                - Compromissos próximos.
                - Possíveis conflitos ou sobrecarga.
                - Recomendações práticas para organizar a rotina.

                Não invente informações.
                Não afirme que uma tarefa está atrasada sem evidência.
                Não altere tarefas ou compromissos.
                IMPORTANTE: Não chame ou invoque nenhuma ferramenta. Todos os dados já foram coletados.

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

                Anotações / Conhecimento Local (RAG):
                {rag_notes or "Nenhuma consulta documental solicitada."}
            """
            ),
        ]
    )
    tools = ["todoist:find-tasks", "google_calendar:events.list"]

    if rag_notes:
        tools.append("rag:chromadb")

    return {
        "todoist_result": tasks_data,
        "calendar_events": events,
        "llm_answer": response.content,
        "tools_used": tools,
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
                IMPORTANTE: Não chame ferramentas.

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
        "tools_used": ["google_calendar:events.list"],
    }
