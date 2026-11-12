import asyncio

from graph.workflow import graph


async def main():
    result = await graph.ainvoke(
        {
            "user_message": "Quais são minhas tarefas de hoje?",
        }
    )

    print("\nResposta do agente:")
    print(result["llm_answer"])

    print("\nDados recebidos do Todoist:")
    print(result.get("todoist_result"))


if __name__ == "__main__":
    asyncio.run(main())
