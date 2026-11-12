import asyncio
from graph.workflow import graph

async def main():
    result = await graph.ainvoke({
        "user_message": "Quais são meus próximos compromissos?"
    })

    print(result["llm_answer"])

asyncio.run(main())