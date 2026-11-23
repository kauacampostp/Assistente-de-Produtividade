import os
import sys
from pathlib import Path

print("Servidor iniciado", file=sys.stderr)

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer

# Localiza a raiz do projeto
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Carrega as variáveis do arquivo .env
load_dotenv(PROJECT_ROOT / ".env")

# Define a pasta que o servidor pode acessar
documents_path = os.getenv("MCP_DOCUMENTS_PATH", "rag/documents")

DOCUMENTS_DIR = Path(documents_path)

if not DOCUMENTS_DIR.is_absolute():
    DOCUMENTS_DIR = PROJECT_ROOT / DOCUMENTS_DIR

DOCUMENTS_DIR = DOCUMENTS_DIR.resolve()

if not DOCUMENTS_DIR.is_dir():
    raise RuntimeError(f"Pasta de documentos não encontrada: {DOCUMENTS_DIR}")


# Inicializa o servidor MCP
mcp = MCPServer("local-files")


# Extensões permitidas nesta primeira versão
ALLOWED_EXTENSIONS = {".md", ".txt"}


# Verifica se o arquivo está dentro da pasta autorizada
def get_safe_file(relative_path: str) -> Path:
    candidate = (DOCUMENTS_DIR / relative_path).resolve()

    try:
        candidate.relative_to(DOCUMENTS_DIR)
    except ValueError:
        raise ValueError("Acesso negado: caminho fora da pasta autorizada.")

    if not candidate.is_file():
        raise FileNotFoundError("Arquivo não encontrado.")

    if candidate.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("Tipo de arquivo não permitido.")

    return candidate


# Tools do mcp. Precisam ter o decorador "@mcp.tool()"
# 1. Listar documentos
@mcp.tool()
def listar_documentos() -> list[str]:
    """
    Lista os arquivos Markdown e TXT disponíveis na base documental.
    Retorna os caminhos relativos à pasta autorizada.
    """
    files = []

    for file in DOCUMENTS_DIR.rglob("*"):
        if not file.is_file():
            continue

        try:
            resolved = file.resolve()
            resolved.relative_to(DOCUMENTS_DIR)
        except ValueError:
            continue

        if resolved.suffix.lower() in ALLOWED_EXTENSIONS:
            files.append(resolved.relative_to(DOCUMENTS_DIR).as_posix())

    return sorted(files)


# 2. Buscar documentos por conteúdo
@mcp.tool()
def buscar_documentos(query: str, max_results: int = 10) -> list[dict]:
    """
    Procura um termo nos conteúdos dos arquivos Markdown e TXT.
    Retorna o nome do arquivo e os trechos encontrados.
    """
    query = query.strip()

    if not query:
        raise ValueError("A busca não pode ser vazia.")

    if len(query) > 200:
        raise ValueError("A busca deve ter no máximo 200 caracteres.")

    if not 1 <= max_results <= 20:
        raise ValueError("max_results deve estar entre 1 e 20.")

    results = []

    for relative_path in listar_documentos():
        if len(results) >= max_results:
            break

        file = get_safe_file(relative_path)

        if file.stat().st_size > 500_000:
            continue

        try:
            content = file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        matching_lines = []

        for line_number, line in enumerate(content.splitlines(), start=1):
            if query.casefold() in line.casefold():
                matching_lines.append(
                    {
                        "line": line_number,
                        "text": line.strip()[:500],
                    }
                )

        if matching_lines:
            results.append(
                {
                    "file": relative_path,
                    "matches": matching_lines[:5],
                }
            )

    return results


# 3. Ler um documento
@mcp.tool()
def ler_documento(relative_path: str) -> str:
    """
    Lê o conteúdo de um arquivo Markdown ou TXT autorizado.
    """
    file = get_safe_file(relative_path)

    # Limita a leitura para evitar arquivos excessivamente grandes
    max_size = 500_000

    if file.stat().st_size > max_size:
        raise ValueError("Arquivo muito grande para leitura (limite: 500 KB).")

    return file.read_text(encoding="utf-8")


# 4. Criar nota
@mcp.tool()
def criar_nota(relative_path: str, content: str) -> str:
    """
    Cria uma nova nota Markdown ou TXT na pasta autorizada.
    Nunca sobrescreve arquivos existentes.
    Exemplo de relative_path: 'Notas/checklist_revisao.md'
    """
    if not relative_path.strip():
        raise ValueError("O caminho não pode ser vazio.")

    if len(content.encode("utf-8")) > 100_000:
        raise ValueError("Conteúdo muito grande (limite: 100 KB).")

    candidate = (DOCUMENTS_DIR / relative_path).resolve()

    try:
        candidate.relative_to(DOCUMENTS_DIR)
    except ValueError:
        raise ValueError("Acesso negado: caminho fora da pasta autorizada.")

    if candidate.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("Tipo de arquivo não permitido (use .md ou .txt).")

    if candidate.exists():
        raise FileExistsError("Já existe um arquivo com esse nome.")

    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(content, encoding="utf-8")

    return f"Nota criada: {candidate.relative_to(DOCUMENTS_DIR).as_posix()}"


# Inicia o servidor utilizando comunicação STDIO (Standard Input/Output)
if __name__ == "__main__":
    mcp.run(transport="stdio")
