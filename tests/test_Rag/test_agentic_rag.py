from rag.workflow import rag_graph

questions = [
    "O que meus documentos dizem sobre ansiedade?",
    "O que significa comunhão?",
    "Como funciona um motor de combustão?",
]

for question in questions:
    print("\n" + "=" * 60)
    print("PERGUNTA:", question)

    result = rag_graph.invoke({"user_message": question})

    print("\nBUSCAS REALIZADAS:", result.get("attempts"))
    print("\nRESPOSTA:")
    print(result["llm_answer"])
