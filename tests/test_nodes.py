from graph.nodes import classify_intent

tests = [
    "Resuma minhas anotações sobre RAG.",
    "Quais tarefas estão atrasadas no Todoist?",
    "Analise minha rotina desta semana.",
    "Organize minha próxima semana."
]

for message in tests:
    state = {
        "user_message": message
    }

    result = classify_intent(state)

    print(f"\nMensagem: {message}")
    print(f"Intenção: {result['intent']}")