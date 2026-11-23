import os

from dotenv import load_dotenv
from groq import BadRequestError
from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY não encontrada no arquivo .env")

_llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
    api_key=api_key,
    max_retries=6,
    reasoning_effort="low",
)

NUDGE = SystemMessage(
    content="Responda apenas com texto. Não chame nenhuma ferramenta ou função."
)


class SafeLLM:
    """Repete a chamada quando o modelo tenta usar ferramenta sem ela estar disponível."""

    def __init__(self, llm, attempts: int = 3):
        self._llm = llm
        self._attempts = attempts

    def invoke(self, messages, **kwargs):
        last_error = None
        msgs = list(messages)

        for _ in range(self._attempts):
            try:
                return self._llm.invoke(msgs, **kwargs)
            except BadRequestError as error:
                if "tool_use_failed" not in str(error):
                    raise
                last_error = error
                # temperature=0 repete o mesmo erro, então muda o prompt
                msgs = list(messages) + [NUDGE]

        raise last_error


LLM = SafeLLM(_llm)
