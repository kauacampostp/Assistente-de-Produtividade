from langchain_core.messages import HumanMessage, SystemMessage

from app import LLM
from rag.retriever import retrieve_documents


# 1. Recupera documentos no ChromaDB
def retrieve(state):
    query = state.get("search_query", state["user_message"])

    documents = retrieve_documents(query, k=4)

    return {
        "retrieved_docs": documents,
        "attempts": state.get("attempts", 0) + 1,
    }


# 2. Avalia se os documentos são relevantes
def grade_documents(state):
    documents = state.get("retrieved_docs", [])

    if not documents:
        return {"documents_relevant": False}

    context = "\n\n".join(document.page_content for document in documents)

    system_prompt = """
    Você é um avaliador de relevância para um sistema RAG.

    Analise a pergunta e os documentos recuperados.

    Decida se os documentos possuem informações úteis
    para responder à pergunta.

    Responda somente:
    SIM
    ou
    NAO
    """

    response = LLM.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=f"""
            Pergunta: {state["user_message"]}

            Documentos:
            {context}
            """
            ),
        ]
    )

    result = response.content.strip().upper()

    return {"documents_relevant": result.startswith("SIM")}


# 3. Reformula a pergunta para uma nova busca
def rewrite_query(state):
    system_prompt = """
    Você é um especialista em reformulação de consultas para RAG.

    Reformule a pergunta para melhorar a recuperação
    de documentos relevantes.

    Preserve a intenção original.
    Utilize termos mais específicos quando possível.

    Retorne somente a nova pergunta.
    """

    response = LLM.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=state["user_message"]),
        ]
    )

    return {"search_query": response.content.strip()}


# 4. Gera uma resposta fundamentada nos documentos
def generate_answer(state):
    documents = state.get("retrieved_docs", [])

    context = "\n\n".join(
        f"""
        Fonte: {document.metadata.get("source", "Fonte desconhecida")}

        Conteúdo:
        {document.page_content}
        """
        for document in documents
    )

    system_prompt = """
    Você é um assistente de conhecimento.

    Responda à pergunta utilizando exclusivamente
    as informações presentes nos documentos fornecidos.

    Regras:
    - Não invente informações.
    - Se os documentos não sustentarem uma afirmação,
      não a apresente como fato.
    - Identifique as fontes utilizadas na resposta,
      mencionando o nome dos arquivos.
    - Responda em português.
    """

    response = LLM.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=f"""
            Pergunta: {state["user_message"]}

            Documentos recuperados:
            {context}
            """
            ),
        ]
    )

    return {"llm_answer": response.content}


# Caso as buscas não encontrem contexto suficiente
def no_context(state):
    return {
        "llm_answer": (
            "Não encontrei informações suficientes nos documentos "
            "para responder com segurança. Tente reformular sua pergunta "
            "ou adicionar documentos à base de conhecimento."
        )
    }
