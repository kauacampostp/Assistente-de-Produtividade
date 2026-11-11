from rag.ingestion import load_documents, split_documents

documents = load_documents()
chunks = split_documents(documents)

print(f"Documentos encontrados: {len(documents)}")
print(f"Chunks gerados: {len(chunks)}")

for chunk in chunks[:3]:
    print("\n--- CHUNK ---")
    print("Origem:", chunk.metadata["source"])
    print("Conteúdo:", chunk.page_content[:300])
