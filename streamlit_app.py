import asyncio
import sqlite3
import uuid

import streamlit as st
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from graph.workflow import build_graph

DB_PATH = "checkpoints.sqlite"


def listar_threads_salvas() -> list[str]:
    """Busca os thread_ids já armazenados no banco SQLite do checkpointer."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("SELECT DISTINCT thread_id FROM checkpoints")
            threads = [row[0] for row in cursor.fetchall() if row[0]]
            return threads or ["conversa-1"]
    except sqlite3.Error:
        return ["conversa-1"]


def extrair_ferramentas_mcp(resultado: dict) -> list[str]:
    """Extrai os nomes das ferramentas MCP usadas a partir do estado retornado pelo grafo."""
    ferramentas: list[str] = []

    # 1. Verifica campos explícitos comuns no estado do LangGraph
    chaves_possiveis = (
        "tools_used",
        "mcp_tools",
        "used_tools",
        "called_tools",
        "ferramentas_usadas",
        "tool_calls",
    )
    for chave in chaves_possiveis:
        valor = resultado.get(chave)
        if isinstance(valor, list):
            for item in valor:
                if isinstance(item, str) and item not in ferramentas:
                    ferramentas.append(item)
                elif isinstance(item, dict):
                    nome = item.get("name") or item.get("tool")
                    if nome and nome not in ferramentas:
                        ferramentas.append(nome)

    # 2. Fallback: verifica mensagens de ferramenta (AIMessage.tool_calls / ToolMessage)
    if not ferramentas:
        for msg in resultado.get("messages", []):
            tool_calls = getattr(msg, "tool_calls", None)
            if isinstance(tool_calls, list):
                for tc in tool_calls:
                    nome = (
                        tc.get("name")
                        if isinstance(tc, dict)
                        else getattr(tc, "name", None)
                    )
                    if nome and nome not in ferramentas:
                        ferramentas.append(nome)
            if getattr(msg, "type", None) == "tool":
                nome = getattr(msg, "name", None)
                if nome and nome not in ferramentas:
                    ferramentas.append(nome)

    return ferramentas


async def carregar_historico_thread(thread_id: str) -> list[dict]:
    """Recupera o histórico salvo no checkpointer para a thread selecionada."""
    async with AsyncSqliteSaver.from_conn_string(DB_PATH) as checkpointer:
        await checkpointer.setup()
        graph = build_graph(checkpointer)
        config = {"configurable": {"thread_id": thread_id}}
        snapshot = await graph.aget_state(config)

        if not snapshot or not snapshot.values:
            return []

        history = snapshot.values.get("conversation_history", [])
        mensagens_ui = []
        for turno in history:
            if "user" in turno:
                mensagens_ui.append({"role": "user", "content": turno["user"]})
            if "assistant" in turno:
                mensagens_ui.append(
                    {
                        "role": "assistant",
                        "content": turno["assistant"],
                        "skill_name": turno.get("skill_name"),
                        "tools_used": turno.get("tools_used", []),
                    }
                )
        return mensagens_ui


async def executar_turno(thread_id: str, mensagem: str) -> dict:
    """Executa uma interação no grafo LangGraph e atualiza o estado persistido."""
    async with AsyncSqliteSaver.from_conn_string(DB_PATH) as checkpointer:
        await checkpointer.setup()
        graph = build_graph(checkpointer)
        config = {"configurable": {"thread_id": thread_id}}

        snapshot = await graph.aget_state(config)
        history = (
            snapshot.values.get("conversation_history", []) if snapshot.values else []
        )

        resultado = await graph.ainvoke(
            {"user_message": mensagem},
            config=config,
        )

        resposta = resultado.get("llm_answer", "Sem resposta.")
        skill_carregada = resultado.get("skill_name")
        ferramentas_usadas = extrair_ferramentas_mcp(resultado)

        history.append(
            {
                "user": mensagem,
                "assistant": resposta,
                "skill_name": skill_carregada,
                "tools_used": ferramentas_usadas,
            }
        )

        await graph.aupdate_state(
            config,
            {"conversation_history": history},
        )

        return {
            "resposta": resposta,
            "skill_name": skill_carregada,
            "tools_used": ferramentas_usadas,
        }


def renderizar_observabilidade(skill_name: str | None, tools_used: list[str]) -> None:
    """Exibe internamente a Skill carregada e as ferramentas MCP acionadas na resposta."""
    with st.expander(
        "🔍 Funcionamento interno (Skills e Ferramentas MCP)", expanded=True
    ):
        skill_texto = f"`{skill_name}`" if skill_name else "`Nenhuma`"
        tools_texto = (
            ", ".join(f"`{ferramenta}`" for ferramenta in tools_used)
            if tools_used
            else "`Nenhuma`"
        )
        st.markdown(f"- **Skill carregada:** {skill_texto}")
        st.markdown(f"- **Ferramentas MCP usadas:** {tools_texto}")


# --- Configuração da página ---
st.set_page_config(
    page_title="Assistente de Produtividade",
    page_icon="🤖",
    layout="centered",
)

# --- Inicialização do estado da sessão ---
if "threads_disponiveis" not in st.session_state:
    st.session_state.threads_disponiveis = listar_threads_salvas()

if "thread_id" not in st.session_state:
    st.session_state.thread_id = st.session_state.threads_disponiveis[0]

if "mensagens" not in st.session_state:
    st.session_state.mensagens = asyncio.run(
        carregar_historico_thread(st.session_state.thread_id)
    )

# --- Barra lateral: controle de conversas (threads) ---
with st.sidebar:
    st.header("💬 Conversas")

    if st.button("➕ Nova conversa", use_container_width=True, type="primary"):
        novo_id = f"conversa-{uuid.uuid4().hex[:6]}"
        st.session_state.threads_disponiveis.insert(0, novo_id)
        st.session_state.thread_id = novo_id
        st.session_state.mensagens = []
        st.rerun()

    st.divider()

    thread_selecionada = st.selectbox(
        "Selecionar conversa existente:",
        options=st.session_state.threads_disponiveis,
        index=st.session_state.threads_disponiveis.index(st.session_state.thread_id),
    )

    if thread_selecionada != st.session_state.thread_id:
        st.session_state.thread_id = thread_selecionada
        st.session_state.mensagens = asyncio.run(
            carregar_historico_thread(thread_selecionada)
        )
        st.rerun()

    custom_id = st.text_input("Ou abrir thread por ID:", placeholder="Ex: conversa-1")
    if st.button("Carregar ID", use_container_width=True) and custom_id.strip():
        tid = custom_id.strip()
        if tid not in st.session_state.threads_disponiveis:
            st.session_state.threads_disponiveis.insert(0, tid)
        st.session_state.thread_id = tid
        st.session_state.mensagens = asyncio.run(carregar_historico_thread(tid))
        st.rerun()

    st.caption(f"Thread ativa: `{st.session_state.thread_id}`")

# --- Área principal do chat ---
st.title("🤖 Assistente de Produtividade")
st.caption(
    "Conhecimento pessoal, tarefas, agenda e planejamento com LangGraph + MCP + Skills"
)

for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            renderizar_observabilidade(
                msg.get("skill_name"),
                msg.get("tools_used", []),
            )

prompt = st.chat_input(
    "Digite sua mensagem (ex: revise minha rotina ou consulte minhas tarefas)..."
)

if prompt:
    st.session_state.mensagens.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Consultando agente..."):
                saida = asyncio.run(executar_turno(st.session_state.thread_id, prompt))

            resposta = saida["resposta"]
            skill = saida["skill_name"]
            tools = saida["tools_used"]

            st.markdown(resposta)
            renderizar_observabilidade(skill, tools)

            st.session_state.mensagens.append(
                {
                    "role": "assistant",
                    "content": resposta,
                    "skill_name": skill,
                    "tools_used": tools,
                }
            )
        except Exception as erro:
            st.error(f"Erro ao executar o assistente: {erro}")
