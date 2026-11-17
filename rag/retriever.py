from rag.vector_store import get_vector_store


# Faz pesquisa no vetor por similaridade (cosseno)
def retrieve_documents(query: str, k: int = 4):
    # Recebe o chroma (banco de dados vetorial)
    vector_store = get_vector_store()

    # Faz a busca por similaridade comparando os vetores
    results = vector_store.similarity_search(
        query=query,
        k=k,
    )

    return results
