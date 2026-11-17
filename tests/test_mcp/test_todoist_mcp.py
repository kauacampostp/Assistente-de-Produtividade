import asyncio

from mcp_servers.clients import list_mcp_tools, todoist_server


async def main():
    tools = await list_mcp_tools(todoist_server())

    selected = {
        "find-tasks",
        "add-tasks",
        "update-tasks",
        "find-projects",
        "add-projects",
        "update-projects",
    }

    for tool in tools:
        if tool.name in selected:
            print(f"\n{'=' * 50}")
            print(tool.name)
            print(tool.model_dump(by_alias=True))


if __name__ == "__main__":
    asyncio.run(main())
