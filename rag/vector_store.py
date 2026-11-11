from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.embeddings import FastEmbedEmbeddings

# Diretório onde o banco vetorial será armazenado
VECTOR_DB_DIR = Path(__file__).parent / "chroma_db"

# Modelo responsável por gerar os embeddings
embeddings = FastEmbedEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)


def get_vector_store():
    return Chroma(
        collection_name="knowledge_base",
        persist_directory=str(VECTOR_DB_DIR),
        embedding_function=embeddings,
    )
