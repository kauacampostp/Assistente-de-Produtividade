
from rag.ingestion import load_documents, split_documents
from rag.vector_store import create_vector_store


# 1. Carrega os documentos
documents = load_documents()

# 2. Divide em chunks
chunks = split_documents(documents)

# 3. Gera embeddings e armazena no ChromaDB
vector_store = create_vector_store(chunks)

print(f"Documentos carregados: {len(documents)}")
print(f"Chunks armazenados: {len(chunks)}")

# 4. Faz uma pesquisa de teste
results = vector_store.similarity_search(
    "O que a Bíblia ensina sobre ansiedade?",
    k=3
)

print("\nResultados da pesquisa:")

for result in results:
    print("\nFonte:", result.metadata["source"])
    print("Conteúdo:", result.page_content[:300])
