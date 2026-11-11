from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

DOCUMENTS_DIR = Path(__file__).parent / "documents"


def load_documents():
    documents = []

    for file_path in DOCUMENTS_DIR.rglob("*.md"):
        content = file_path.read_text(encoding="utf-8")

        if not content.strip():
            continue

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


def split_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = text_splitter.split_documents(documents)

    return chunks
