"""
Canonicalização de números de telefone brasileiros.

Usado para reconhecer um aluno recorrente pelo número de WhatsApp: o Chatwoot
entrega o telefone em formatos variados (`+55 91 99174-4186`, `5591991744186`,
`wa_id` cru), e precisamos de UMA forma estável para usar como chave.

Forma canônica: apenas dígitos, com DDI, sem `+` — `5591991744186`.

Nada aqui toca banco, rede ou settings: são funções puras, importáveis pelo
chatbot e pelos testes sem arrastar dependências.
"""
from __future__ import annotations

import re
from typing import Optional

# DDDs válidos no Brasil (Anatel). Serve para rejeitar lixo que por acaso tenha
# a quantidade certa de dígitos.
_DDD_VALIDOS = frozenset({
    11, 12, 13, 14, 15, 16, 17, 18, 19,
    21, 22, 24, 27, 28,
    31, 32, 33, 34, 35, 37, 38,
    41, 42, 43, 44, 45, 46, 47, 48, 49,
    51, 53, 54, 55,
    61, 62, 63, 64, 65, 66, 67, 68, 69,
    71, 73, 74, 75, 77, 79,
    81, 82, 83, 84, 85, 86, 87, 88, 89,
    91, 92, 93, 94, 95, 96, 97, 98, 99,
})

_DDI_BR = "55"


def normalizar_telefone(raw: Optional[str]) -> Optional[str]:
    """
    Devolve o telefone na forma canônica `55DDNNNNNNNNN`, ou `None`.

    Regras:
      • remove tudo que não é dígito e o `00` de discagem internacional;
      • 10 ou 11 dígitos  → assume Brasil e prefixa `55`;
      • 12 ou 13 dígitos começando com `55` → mantém;
      • qualquer outra coisa → `None`.

    Nunca "conserta" um número: se não der para afirmar o que é, devolve `None`.
    Reconhecer errado é pior do que não reconhecer — o bot cumprimentaria um
    desconhecido pelo nome de um aluno.
    """
    if not raw:
        return None

    digitos = re.sub(r"\D", "", str(raw))
    if digitos.startswith("00"):
        digitos = digitos[2:]

    if len(digitos) in (10, 11):
        digitos = _DDI_BR + digitos
    elif len(digitos) in (12, 13):
        if not digitos.startswith(_DDI_BR):
            return None  # outro país: não sabemos tratar
    else:
        return None

    ddd = int(digitos[2:4])
    if ddd not in _DDD_VALIDOS:
        return None

    assinante = digitos[4:]
    # Fixo tem 8 dígitos; celular tem 9 e começa com 9.
    if len(assinante) == 9 and not assinante.startswith("9"):
        return None

    return digitos


def variantes_telefone(canonico: Optional[str]) -> list[str]:
    """
    Formas equivalentes do mesmo número, para busca.

    O 9º dígito é a armadilha real: o `wa_id` que o provedor de WhatsApp entrega
    para celular brasileiro às vezes vem sem o `9` inicial do assinante
    (`559191744186` em vez de `5591991744186`). Gravamos sempre a forma com 9;
    a busca aceita as duas.
    """
    if not canonico:
        return []

    variantes = [canonico]
    assinante = canonico[4:]

    if len(assinante) == 9 and assinante.startswith("9"):
        variantes.append(canonico[:4] + assinante[1:])   # tira o 9
    elif len(assinante) == 8:
        variantes.append(canonico[:4] + "9" + assinante)  # põe o 9

    return variantes


def mascarar_telefone(canonico: Optional[str]) -> str:
    """
    `5591991744186` → `+55 91 *****-4186`.

    É a ÚNICA forma permitida de um telefone aparecer em log ou em nota para
    atendente: o suficiente para conferir, insuficiente para vazar.
    """
    if not canonico:
        return "?"
    if len(canonico) < 8:
        return "***"
    return f"+{canonico[:2]} {canonico[2:4]} *****-{canonico[-4:]}"
