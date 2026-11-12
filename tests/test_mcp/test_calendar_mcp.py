import asyncio

from mcp_servers.clients import list_google_calendar_tools


async def main():
    tools = await list_google_calendar_tools()

    print("Ferramentas do Google Calendar:\n")

    for tool in tools:
        print(f"- {tool.name}: {tool.description}")
        print("Schema:", tool.input_schema)


if __name__ == "__main__":
    asyncio.run(main())
