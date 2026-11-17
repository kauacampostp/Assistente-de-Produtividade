import asyncio

from graph.workflow import graph


async def main():
    state = {}

    print("Assistente de Produtividade iniciado!")
    print("Digite 'sair' para encerrar.\n")

    while True:
        mensagem = input("Você: ").strip()

        if mensagem.lower() == "sair":
            break

        state["user_message"] = mensagem

        resultado = await graph.ainvoke(state)

        # Preserva o estado retornado pelo LangGraph
        state.update(resultado)
        print("Skill carregada:", resultado.get("skill_name") or "Nenhuma")

        print("\nAssistente:", resultado.get("llm_answer", "Sem resposta."))
        print()


if __name__ == "__main__":
    asyncio.run(main())
