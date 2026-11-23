import re

MAX_INPUT_LENGTH = 4000

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"ignore\s+(todas\s+as\s+)?instruções\s+(anteriores|acima)",
    r"desconsidere\s+(todas\s+as\s+)?instruções\s+(anteriores|acima)",
    r"reveal\s+(your\s+)?(system\s+)?prompt",
    r"revele\s+(seu\s+)?prompt\s+(interno|de\s+sistema)",
    r"mostre\s+(seu\s+)?prompt\s+(interno|de\s+sistema)",
    r"exiba\s+(seu\s+)?prompt\s+(interno|de\s+sistema|completo)",
    r"ignore\s+(as\s+)?regras\s+de\s+segurança",
    r"contorne\s+(as\s+)?(regras|restrições|proteções)",
    r"bypass\s+(the\s+)?(security|safety|restrictions)",
]

SENSITIVE_REQUEST_PATTERNS = [
    r"\btoken\.json\b",
    r"\bcredentials\.json\b",
    r"(^|\s)\.env(\s|$|\b)",
    r"\bGROQ_API_KEY\b",
    r"\bTODOIST_API_TOKEN\b",
    r"conteúdo\s+bruto\s+do\s+arquivo\s+.*(token|credencial|secret|env)",
    r"(apague|delete|exclua|remova)\s+todas?\s+.*sem\s+(pedir\s+)?confirmação",
]


def validate_input(message: str) -> tuple[bool, str | None]:
    """Valida a entrada antes de encaminhá-la ao agente."""

    if not isinstance(message, str):
        return False, "A mensagem precisa ser um texto."

    message = message.strip()

    if not message:
        return False, "A mensagem não pode estar vazia."

    if len(message) > MAX_INPUT_LENGTH:
        return False, (
            f"A mensagem ultrapassa o limite de {MAX_INPUT_LENGTH} caracteres."
        )

    if detect_prompt_injection(message):
        return False, (
            "Mensagem bloqueada pelo controle de segurança: "
            "foi identificada uma possível tentativa de "
            "manipular as instruções internas do agente."
        )

    if detect_unsafe_operation_or_secret_access(message):
        return False, (
            "Solicitação bloqueada pelo controle de segurança: "
            "não é permitido exibir arquivos de credenciais/tokens nem "
            "executar exclusões em massa sem confirmação explícita."
        )

    return True, None


def detect_prompt_injection(message: str) -> bool:
    """Detecta padrões explícitos de tentativa de prompt injection."""

    return any(
        re.search(pattern, message, re.IGNORECASE) for pattern in INJECTION_PATTERNS
    )


def detect_unsafe_operation_or_secret_access(message: str) -> bool:
    """Detecta tentativas de acesso a arquivos secretos ou exclusão sem confirmação."""

    return any(
        re.search(pattern, message, re.IGNORECASE)
        for pattern in SENSITIVE_REQUEST_PATTERNS
    )
