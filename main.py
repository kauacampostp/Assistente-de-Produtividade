from graph.workflow import graph

mesagem = input("Digite sua mensagem: ")
resultado = graph.invoke({"user_message": mesagem})

print("\nIntenção identificada;", resultado["intent"])
print("Resposta:", resultado["llm_answer"])
