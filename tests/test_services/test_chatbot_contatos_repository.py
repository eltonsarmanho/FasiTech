"""Testes das funções de banco do diretório de contatos do chatbot.

Isolamento: em vez de depender do engine global (que aponta para o Postgres
real conforme `DATABASE_URL`), criamos um SQLite em memória e trocamos
`get_db_session` por uma sessão sobre ele. O flag de schema é marcado como
pronto para que `_ensure_chatbot_contatos_schema` não tente inspecionar o
engine global. Assim estes testes rodam offline e sem tocar em dado real.
"""
from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, select, create_engine

from backend.infrastructure.database import repository as repo
from backend.infrastructure.database.models import ChatbotContatoConhecido

CANAL = "whatsapp"
TELEFONE = "5591991744186"
TELEFONE_SEM_9 = "559191744186"
MATRICULA = "202316040021"
NOME = "Vitor Benedito Ribeiro Batista"
EMAIL = "vitor.batista@cameta.ufpa.br"


@pytest.fixture
def banco(monkeypatch):
    """SQLite em memória com apenas a tabela do diretório."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    ChatbotContatoConhecido.__table__.create(engine)

    monkeypatch.setattr(repo, "get_db_session", lambda: Session(engine))
    monkeypatch.setattr(repo, "_chatbot_contatos_schema_ready", True)
    return engine


def _gravar(**overrides) -> int:
    dados = dict(
        canal=CANAL, chave=TELEFONE, matricula=MATRICULA, nome=NOME, email=EMAIL
    )
    dados.update(overrides)
    return repo.upsert_chatbot_contato_conhecido(**dados)


# ── Gravação e leitura ────────────────────────────────────────────────────────

def test_grava_e_encontra(banco):
    _gravar(chatwoot_contact_id=42, ticket_id="TKT-ABC12345")

    achado = repo.buscar_chatbot_contato_conhecido(CANAL, [TELEFONE])
    assert achado is not None
    assert achado["matricula"] == MATRICULA
    assert achado["nome"] == NOME
    assert achado["email"] == EMAIL
    assert achado["chatwoot_contact_id"] == 42
    assert achado["ultimo_ticket_id"] == "TKT-ABC12345"
    assert achado["ativo"] is True
    assert achado["origem"] == "chatbot"
    assert achado["ultimo_atendimento_em"] is not None


def test_contato_inexistente_devolve_none(banco):
    assert repo.buscar_chatbot_contato_conhecido(CANAL, ["5511999999999"]) is None


def test_busca_por_variante_sem_o_nono_digito(banco):
    """O provedor pode entregar o wa_id sem o 9 — a busca aceita as duas formas."""
    _gravar(chave=TELEFONE)
    achado = repo.buscar_chatbot_contato_conhecido(CANAL, [TELEFONE_SEM_9, TELEFONE])
    assert achado is not None and achado["matricula"] == MATRICULA


def test_ordem_das_chaves_e_preferencia(banco):
    """Havendo linhas para as duas formas, a primeira chave da lista vence."""
    _gravar(chave=TELEFONE, matricula="202316040021")
    _gravar(chave=TELEFONE_SEM_9, matricula="209900000000")

    achado = repo.buscar_chatbot_contato_conhecido(CANAL, [TELEFONE_SEM_9, TELEFONE])
    assert achado["matricula"] == "209900000000"


def test_busca_isola_por_canal(banco):
    _gravar()
    assert repo.buscar_chatbot_contato_conhecido("email", [TELEFONE]) is None


@pytest.mark.parametrize("canal,chaves", [("", [TELEFONE]), (CANAL, []), (None, None)])
def test_busca_com_argumentos_vazios(banco, canal, chaves):
    assert repo.buscar_chatbot_contato_conhecido(canal, chaves) is None


# ── Upsert ────────────────────────────────────────────────────────────────────

def test_upsert_atualiza_em_vez_de_duplicar(banco):
    primeiro = _gravar()
    segundo = _gravar(nome="Vitor B. R. Batista", email="novo@ufpa.br")

    assert primeiro == segundo
    achado = repo.buscar_chatbot_contato_conhecido(CANAL, [TELEFONE])
    assert achado["nome"] == "Vitor B. R. Batista"
    assert achado["email"] == "novo@ufpa.br"

    with Session(banco) as s:
        assert len(s.exec(select(ChatbotContatoConhecido)).all()) == 1


def test_chave_duplicada_no_mesmo_canal_e_barrada_pelo_banco(banco):
    """A constraint única é a rede de segurança sob o upsert."""
    _gravar()
    with Session(banco) as s:
        s.add(ChatbotContatoConhecido(
            canal=CANAL, chave=TELEFONE, matricula="209900000000",
            nome="Outra Pessoa", email="outra@ufpa.br",
        ))
        with pytest.raises(IntegrityError):
            s.commit()


def test_mesma_chave_em_canais_diferentes_convive(banco):
    _gravar()
    _gravar(canal="email", chave=EMAIL)
    assert repo.buscar_chatbot_contato_conhecido(CANAL, [TELEFONE]) is not None
    assert repo.buscar_chatbot_contato_conhecido("email", [EMAIL]) is not None


def test_aluno_pode_ter_dois_telefones(banco):
    _gravar(chave="5591991744186")
    _gravar(chave="5511987654321")
    for chave in ("5591991744186", "5511987654321"):
        assert repo.buscar_chatbot_contato_conhecido(CANAL, [chave])["matricula"] == MATRICULA


# ── Confirmação ───────────────────────────────────────────────────────────────

def test_confirmacao_incrementa_e_renova_a_janela(banco):
    _gravar()
    antes = repo.buscar_chatbot_contato_conhecido(CANAL, [TELEFONE])

    repo.registrar_confirmacao_chatbot_contato(CANAL, TELEFONE, ticket_id="TKT-NOVO0001")

    depois = repo.buscar_chatbot_contato_conhecido(CANAL, [TELEFONE])
    assert depois["confirmacoes"] == antes["confirmacoes"] + 1
    assert depois["ultimo_ticket_id"] == "TKT-NOVO0001"
    assert depois["ultimo_atendimento_em"] >= antes["ultimo_atendimento_em"]


def test_confirmacao_de_contato_inexistente_nao_quebra(banco):
    repo.registrar_confirmacao_chatbot_contato(CANAL, "5511900000000", ticket_id="TKT-X")


# ── Desativação ───────────────────────────────────────────────────────────────

def test_desativar_esconde_da_busca_mas_preserva_historico(banco):
    _gravar()
    repo.desativar_chatbot_contato_conhecido(CANAL, TELEFONE)

    assert repo.buscar_chatbot_contato_conhecido(CANAL, [TELEFONE]) is None

    with Session(banco) as s:
        linha = s.exec(select(ChatbotContatoConhecido)).one()
        assert linha.ativo is False
        assert linha.negacoes == 1
        assert linha.matricula == MATRICULA  # histórico preservado


def test_negacoes_acumulam(banco):
    _gravar()
    repo.desativar_chatbot_contato_conhecido(CANAL, TELEFONE)
    repo.desativar_chatbot_contato_conhecido(CANAL, TELEFONE)
    with Session(banco) as s:
        assert s.exec(select(ChatbotContatoConhecido)).one().negacoes == 2


def test_numero_reciclado_se_cura_com_nova_identificacao(banco):
    """
    O dono antigo negou (vínculo desativado). O novo dono se identifica
    manualmente: o upsert sobrescreve os dados e reativa a linha.
    """
    _gravar()
    repo.desativar_chatbot_contato_conhecido(CANAL, TELEFONE)

    _gravar(matricula="202412340001", nome="Maria Souza", email="maria@ufpa.br")

    achado = repo.buscar_chatbot_contato_conhecido(CANAL, [TELEFONE])
    assert achado is not None
    assert achado["matricula"] == "202412340001"
    assert achado["nome"] == "Maria Souza"
    assert achado["ativo"] is True
    assert achado["negacoes"] == 0, "reidentificação zera o histórico de negação"


def test_desativar_contato_inexistente_nao_quebra(banco):
    repo.desativar_chatbot_contato_conhecido(CANAL, "5511900000000")
