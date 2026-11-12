import asyncio

from graph.workflow import graph


async def main():
    perguntas = [
        "Quais documentos estão disponíveis?",
        "Quais são minhas tarefas de hoje?",
    ]

    for pergunta in perguntas:
        print(f"\nPergunta: {pergunta}")

        resultado = await graph.ainvoke({"user_message": pergunta})

        print("Resposta:")
        print(resultado["llm_answer"])


if __name__ == "__main__":
    asyncio.run(main())
