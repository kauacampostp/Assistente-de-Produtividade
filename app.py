import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY não encontrada no arquivo .env")

LLM = ChatGroq(model="openai/gpt-oss-20b", temperature=0, api_key=api_key)
