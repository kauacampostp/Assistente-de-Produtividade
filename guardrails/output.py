import re

MAX_OUTPUT_LENGTH = 12000

SENSITIVE_PATTERNS = [
    # Chaves de API comuns
    r"\bgsk_[A-Za-z0-9]{20,}\b",
    r"\bsk-[A-Za-z0-9_-]{20,}\b",
    # Tokens de autenticação
    r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{15,}",
    # Variáveis e campos JSON contendo credenciais
    r"(?i)['\"]?(api[_-]?key|secret[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|token|password)['\"]?"
    r"\s*[:=]\s*['\"]?[^'\"\s,;}{]{8,}",
    # Chaves privadas
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----.*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
]


def sanitize_sensitive_data(text: str) -> str:
    """Remove possíveis credenciais e segredos da resposta."""

    for pattern in SENSITIVE_PATTERNS:
        text = re.sub(
            pattern,
            "[DADO SENSÍVEL REMOVIDO]",
            text,
            flags=re.DOTALL,
        )

    return text


def validate_output(response: str) -> str:
    """Valida e sanitiza a resposta antes de exibi-la."""

    if not isinstance(response, str):
        return "Não foi possível gerar uma resposta válida."

    response = response.strip()

    if not response:
        return "O assistente não gerou uma resposta."

    # Limitar tamanho da resposta
    if len(response) > MAX_OUTPUT_LENGTH:
        response = (
            response[:MAX_OUTPUT_LENGTH]
            + "\n\n[Resposta limitada pelo controle de saída.]"
        )

    # Remover possíveis credenciais
    response = sanitize_sensitive_data(response)

    return response
