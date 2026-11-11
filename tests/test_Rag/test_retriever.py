
from rag.retriever import retrieve_documents


query = "Como lidar com a ansiedade?"

documents = retrieve_documents(query, k=4)

print(f"Documentos recuperados: {len(documents)}")

for i, document in enumerate(documents, start=1):
    print(f"\n--- Resultado {i} ---")
    print("Fonte:", document.metadata.get("source"))
    print("Conteúdo:", document.page_content[:500])
