from rag.vector_store import get_vector_store


def retrieve_documents(query: str, k: int = 4):
    vector_store = get_vector_store()

    results = vector_store.similarity_search(
        query=query,
        k=k,
    )

    return results
