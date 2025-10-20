from __future__ import annotations

import re

CPF_PATTERN = re.compile(r"\d{11}")


def is_valid_cpf(cpf: str) -> bool:
    """Valida formato básico de CPF (11 dígitos).

    Nota: Adicione regras completas posteriormente.
    """
    digits = re.sub(r"\D", "", cpf)
    return bool(CPF_PATTERN.fullmatch(digits))
