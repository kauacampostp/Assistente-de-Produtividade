import asyncio
import os

from mcp import Client, StdioServerParameters

server = StdioServerParameters(
    command="npx",
    args=["-y", "mcp-remote", "https://ai.todoist.net/mcp"],
    env=os.environ.copy(),
)


async def main():
    async with Client(server) as client:
        # Descobrir ferramentas
        result = await client.list_tools()
        tools = result.tools

        print(f"Total de ferramentas: {len(tools)}")

        # Consultar estrutura do Todoist
        result = await client.call_tool("get-overview", {})

        print("\nEstrutura do Todoist:")
        for content in result.content:
            if hasattr(content, "text"):
                print(content.text)


if __name__ == "__main__":
    asyncio.run(main())
