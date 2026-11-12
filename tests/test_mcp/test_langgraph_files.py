import asyncio

from mcp_servers.clients import (
    call_mcp_tool,
    local_files_server,
)


async def main():
    result = await call_mcp_tool(
        local_files_server(),
        "listar_documentos",
    )

    print("Documentos disponíveis:")
    for item in result:
        if hasattr(item, "text"):
            print(item.text)


if __name__ == "__main__":
    asyncio.run(main())
