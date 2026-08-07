"""Testes de canonicalização de telefone (`backend/utils/phone.py`).

O reconhecimento de aluno recorrente usa o telefone como chave. Normalizar
errado tem consequência concreta: o bot cumprimentaria um desconhecido pelo
nome de um aluno. Por isso a regra é "na dúvida, devolve None" — e é isso que
os casos negativos aqui protegem.

Os formatos ruins vieram de dados reais de `requerimento_tcc_submissions.telefone`.
"""
from __future__ import annotations

import pytest

from backend.utils.phone import (
    mascarar_telefone,
    normalizar_telefone,
    variantes_telefone,
)

CANONICO = "5591991744186"


# ── Aceita ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "entrada",
    [
        "+5591991744186",
        "5591991744186",
        "+55 (91) 99174-4186",
        "+55 91 99174 4186",
        "91 99174 4186",
        "(91) 99174-4186",
        "91991744186",
        "005591991744186",
        " 91991744186 ",
    ],
)
def test_formatos_equivalentes_dao_a_mesma_chave(entrada):
    assert normalizar_telefone(entrada) == CANONICO


@pytest.mark.parametrize(
    "entrada,esperado",
    [
        ("(91) 99303-7140", "5591993037140"),
        ("91991163331", "5591991163331"),
        ("91 3201-1000", "559132011000"),      # fixo, 8 dígitos
        ("11 98765-4321", "5511987654321"),
    ],
)
def test_outros_numeros_validos(entrada, esperado):
    assert normalizar_telefone(entrada) == esperado


# ── Rejeita ───────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "entrada,motivo",
    [
        ("", "vazio"),
        (None, "None"),
        ("   ", "só espaços"),
        ("abc", "sem dígitos"),
        ("12345", "curto demais"),
        ("991744186", "9 dígitos, sem DDD"),
        ("00 99174-4186", "DDD 00 não existe"),
        ("(20) 99174-4186", "DDD 20 não existe"),
        ("4491991744186", "DDI de outro país (UK)"),
        ("5591891744186", "celular de 9 dígitos que não começa com 9"),
        ("559199174418612345", "longo demais"),
    ],
)
def test_entradas_invalidas_devolvem_none(entrada, motivo):
    assert normalizar_telefone(entrada) is None, f"deveria rejeitar: {motivo}"


def test_numero_ambiguo_do_banco_legado_e_aceito_como_fixo():
    """
    `"91 74000039"` existe em `requerimento_tcc_submissions.telefone`. Parece
    truncado, mas estruturalmente é DDD 91 + 8 dígitos — indistinguível de um
    fixo válido. Não dá para rejeitá-lo sem uma regra que também rejeitaria
    telefones legítimos de WhatsApp cujo `wa_id` vem sem o 9º dígito, que é
    justamente o caso que `variantes_telefone` existe para cobrir.

    Este teste fixa a decisão: a proteção contra dados sujos NÃO é a
    normalização, é não popular o diretório a partir daquela tabela. Só entra
    ali telefone que chegou pelo próprio canal do WhatsApp.
    """
    assert normalizar_telefone("91 74000039") == "559174000039"


def test_wa_id_sem_o_nono_digito_continua_valido():
    """A regra acima tem um preço, e é este caso que ela paga."""
    assert normalizar_telefone("559191744186") == "559191744186"


# ── Variantes (o 9º dígito) ───────────────────────────────────────────────────

def test_variantes_cobrem_o_nono_digito():
    assert variantes_telefone(CANONICO) == [CANONICO, "559191744186"]


def test_variantes_a_partir_da_forma_sem_o_nono_digito():
    assert variantes_telefone("559191744186") == ["559191744186", "5591991744186"]


def test_variantes_de_fixo_acrescentam_a_forma_movel():
    # 8 dígitos: a heurística tenta a forma com 9 — busca mais ampla, nunca menos.
    assert variantes_telefone("559132011000")[0] == "559132011000"


@pytest.mark.parametrize("entrada", [None, ""])
def test_variantes_de_vazio(entrada):
    assert variantes_telefone(entrada) == []


def test_variante_canonica_vem_sempre_primeiro():
    """A ordem é preferência de match — a forma exata tem que ganhar."""
    for numero in (CANONICO, "559191744186"):
        assert variantes_telefone(numero)[0] == numero


# ── Máscara ───────────────────────────────────────────────────────────────────

def test_mascara_esconde_o_miolo():
    mascarado = mascarar_telefone(CANONICO)
    assert mascarado == "+55 91 *****-4186"
    # O que não pode vazar: os dígitos do meio.
    assert "99174" not in mascarado
    assert CANONICO not in mascarado


@pytest.mark.parametrize("entrada,esperado", [(None, "?"), ("", "?"), ("123", "***")])
def test_mascara_com_entrada_degenerada(entrada, esperado):
    assert mascarar_telefone(entrada) == esperado
