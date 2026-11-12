from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Pega os arquivos da pasta "documents"
DOCUMENTS_DIR = Path(__file__).parent / "documents"


# Carrega todos os documentos presente na pasta para um array
def load_documents():
    documents = []

    # rglob(*.md) serve para selecionar todos os arquivos .md mesmo dentro de pastas
    for file_path in DOCUMENTS_DIR.rglob("*.md"):
        content = file_path.read_text(encoding="utf-8")

        if not content.strip():
            continue

        # Salva documento com função do LangChain (Document)
        document = Document(
            page_content=content,
            metadata={
                "source": str(file_path.relative_to(DOCUMENTS_DIR)),
                "category": file_path.parent.name,
                "file_name": file_path.name,
            },
        )

        documents.append(document)
    return documents


# Criar chunks (partes da divisão do texto)
def split_documents(documents):
    # size = tamanho de cada parte, overlap = sobreposição para manter conecxão das partes
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = text_splitter.split_documents(documents)

    return chunks
