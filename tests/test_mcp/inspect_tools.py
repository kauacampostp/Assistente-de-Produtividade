import asyncio

from mcp_servers.clients import (
    list_mcp_tools,
    local_files_server,
    todoist_server,
)


async def main():
    servers = {
        "ARQUIVOS": local_files_server(),
        "TODOIST": todoist_server(),
    }

    for name, server in servers.items():
        print(f"\n--- {name} ---")

        tools = await list_mcp_tools(server)

        for tool in tools:
            print(f"\n{tool.name}")
            print(tool.description)
            print(tool.input_schema)


if __name__ == "__main__":
    asyncio.run(main())
