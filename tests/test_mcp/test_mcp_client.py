import asyncio
import os
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

PROJECT_ROOT = Path(__file__).resolve().parents[2]

server = StdioServerParameters(
    command="/usr/bin/python",
    args=[str(PROJECT_ROOT / "mcp_servers" / "local_files" / "server.py")],
    env=os.environ.copy(),
)


async def main():
    async with Client(server) as client:
        # 1. Descobrir as ferramentas disponíveis
        tools = await client.list_tools()

        print("FERRAMENTAS DISPONÍVEIS:")
        for tool in tools.tools:
            print(f"- {tool.name}: {tool.description}")

        # 2. Testar listagem de documentos
        print("\nTESTE: listar_documentos")
        result = await client.call_tool("listar_documentos", {})
        print(result.content)

        # 3. Testar busca por conteúdo
        print("\nTESTE: buscar_documentos")
        result = await client.call_tool(
            "buscar_documentos",
            {"query": "ansiedade", "max_results": 5},
        )
        print(result.content)

        # 4. Testar leitura de documento
        print("\nTESTE: ler_documento")
        result = await client.call_tool(
            "ler_documento",
            {"relative_path": "Sermons/Ansiedade - Fp 4 6-9.md"},
        )
        print(result.content)

        # 5. Testar bloqueio de acesso externo
        print("\nTESTE: proteção de diretório")
        result = await client.call_tool(
            "ler_documento",
            {"relative_path": "../../.env"},
        )

        print("Acesso bloqueado:", result.is_error)


if __name__ == "__main__":
    asyncio.run(main())
