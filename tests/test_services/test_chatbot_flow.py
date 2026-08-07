"""Testes do fluxo de atendimento do Diretor Virtual (chatbot_service.py).

Regressão principal (bug relatado em produção):

    Bot: "Para qual período letivo você deseja as informações? (2026.1 … 2026.4)"
    Aluno: "2026.4"
    Bot: ❌ escalava para a Secretaria

O antigo parser de menu lia `msg.strip()[:1]` — o "2" de "2026.4" virava a opção
"2 = Falar com Secretário". A causa raiz era o estado: o pedido de esclarecimento
do RAG voltava para MENU em vez de aguardar a resposta do aluno.

O RAG é substituído por um duplo em todos os testes: aqui se valida a máquina de
estados do atendimento, não a qualidade da resposta.
"""
from __future__ import annotations

import sys
import types

import pytest

from backend.infrastructure.chatbot import chatbot_service as cs
from backend.infrastructure.chatbot.chatbot_service import (
    ChatSession,
    ChatState,
    process_message,
)

# ── Dados de teste (aluno real do cenário relatado) ───────────────────────────

MATRICULA = "202316040021"
NOME = "Vitor Benedito Ribeiro Batista"
EMAIL = "vitor.batista@cameta.ufpa.br"
PERGUNTA = (
    "Gostaria de saber se existe algum prazo pra matrícula na disciplina de "
    "Estágio? Acompanha o mesmo prazo do sistema? Ou tem alguma data específica?"
)
PERIODO = "2026.4"

CLARIFICACAO = (
    "Para qual **período letivo** você deseja as informações?\n\n"
    "Períodos disponíveis nos documentos: **2026.1, 2026.2, 2026.3, 2026.4**\n\n"
    "Por favor, especifique o período (ex.: *2026.2*)."
)
RESPOSTA_FINAL = (
    "O prazo de matrícula em Estágio no período 2026.4 vai de 10/03 a 20/03, "
    "conforme o calendário acadêmico."
)


# ── Duplos de teste ───────────────────────────────────────────────────────────

class FakeRag:
    """Substitui `_call_rag`. Pede esclarecimento até a pergunta citar o período."""

    def __init__(self, *, answer: str = RESPOSTA_FINAL, always_clarify: bool = False):
        self.answer = answer
        self.always_clarify = always_clarify
        self.calls: list[str] = []

    def __call__(self, question: str, session_id: str | None = None) -> dict:
        self.calls.append(question)
        if self.always_clarify or not cs._extract_period(question):
            return {"answer": CLARIFICACAO, "needs_clarification": True}
        return {"answer": self.answer, "needs_clarification": False}


@pytest.fixture
def rag(monkeypatch) -> FakeRag:
    fake = FakeRag()
    monkeypatch.setattr(cs, "_call_rag", fake)
    return fake


@pytest.fixture
def chatwoot(monkeypatch) -> dict:
    """Intercepta as chamadas ao Chatwoot feitas por `_escalate`."""
    from backend.infrastructure.chatwoot import chatwoot_service as cw

    captured: dict = {"escalations": [], "notes": []}

    def _escalate_to_team(**kwargs):
        captured["escalations"].append(kwargs)
        return 999

    monkeypatch.setattr(cw, "escalate_to_team", _escalate_to_team)
    monkeypatch.setattr(cw, "assign_team", lambda conv, team: captured["escalations"].append(
        {"conversation_id": conv, "team_id": team}
    ))
    monkeypatch.setattr(cw, "send_message", lambda conv, content, private=False: captured["notes"].append(content))
    return captured


def _identified_session() -> ChatSession:
    """Sessão que já passou pelo fluxo de ticket e está no menu."""
    sess = ChatSession(session_id="sess-test")
    process_message(sess, MATRICULA)
    process_message(sess, NOME)
    process_message(sess, EMAIL)
    assert sess.state == ChatState.MENU
    return sess


# ── 1. Fluxo de ticket (deve permanecer igual) ────────────────────────────────

def test_fluxo_de_ticket_registra_e_abre_menu():
    sess = ChatSession(session_id="s1")

    r = process_message(sess, MATRICULA)
    assert sess.state == ChatState.AWAITING_NOME
    assert "nome completo" in r["response"].lower()

    r = process_message(sess, NOME)
    assert sess.state == ChatState.AWAITING_EMAIL

    r = process_message(sess, EMAIL)
    assert sess.state == ChatState.MENU
    assert r["ticket_id"] and r["ticket_id"].startswith("TKT-")
    assert sess.matricula == MATRICULA
    assert sess.nome == NOME
    assert sess.email == EMAIL
    assert r["options"] == [
        "1 - Fazer uma pergunta",
        "2 - Falar com Secretário",
        "3 - Falar com Diretor",
        "4 - Encerrar",
    ]


@pytest.mark.parametrize(
    "entrada",
    ["123", "20231604002", "abcdefghijkl", "2023.1604.0021", ""],
)
def test_matricula_invalida_nao_avanca(entrada):
    sess = ChatSession(session_id="s2")
    process_message(sess, entrada)
    assert sess.state == ChatState.AWAITING_MATRICULA


def test_ajuda_progressiva_apos_tentativas_invalidas():
    sess = ChatSession(session_id="s3")
    r1 = process_message(sess, "123")
    r3 = None
    for _ in range(2):
        r3 = process_message(sess, "123")
    assert "SIGAA" not in r1["response"]
    assert "SIGAA" in r3["response"]
    assert sess.state == ChatState.AWAITING_MATRICULA


# ── 2. Regressão: esclarecimento não pode escalar ─────────────────────────────

def test_cenario_relatado_ponta_a_ponta(rag, chatwoot):
    """Reproduz exatamente a conversa das capturas de tela."""
    sess = _identified_session()

    # Opção 1 → bot pede a dúvida
    r = process_message(sess, "1")
    assert sess.state == ChatState.ASKING_QUESTION

    # Pergunta ambígua no tempo → RAG pede o período letivo
    r = process_message(sess, PERGUNTA)
    assert sess.state == ChatState.AWAITING_CLARIFICATION
    assert "período letivo" in r["response"]
    # ❗ O menu NÃO pode aparecer: é ele que fazia "2026.4" virar a opção "2".
    assert r["options"] is None
    assert "Falar com Secretário" not in r["response"]

    # Aluno responde o período → deve ser RESPOSTA, não escalação
    r = process_message(sess, PERIODO)
    assert sess.state == ChatState.MENU, "resposta ao esclarecimento não pode escalar"
    assert chatwoot["escalations"] == [], "nenhuma escalação deveria ter ocorrido"
    assert RESPOSTA_FINAL in r["response"]
    assert r["options"] is not None  # menu volta só depois da resposta

    # O RAG recebeu a pergunta original + o período (contexto preservado)
    assert "Estágio" in rag.calls[-1]
    assert PERIODO in rag.calls[-1]


@pytest.mark.parametrize("resposta", ["2026.4", "2026.1", " 2026.4 ", "2026/4", "período 2026.4"])
def test_periodo_informado_nunca_escala(rag, chatwoot, resposta):
    sess = _identified_session()
    process_message(sess, "1")
    process_message(sess, PERGUNTA)
    assert sess.state == ChatState.AWAITING_CLARIFICATION

    process_message(sess, resposta)
    assert sess.state != ChatState.ESCALATED
    assert chatwoot["escalations"] == []


def test_esclarecimento_sem_periodo_esgota_tentativas_e_oferece_humano(monkeypatch, chatwoot):
    """Loop de no-match tem fim: volta ao menu com caminho humano, sem escalar sozinho."""
    monkeypatch.setattr(cs, "_call_rag", FakeRag(always_clarify=True))
    sess = _identified_session()
    process_message(sess, "1")
    process_message(sess, PERGUNTA)

    r = process_message(sess, "não sei")
    assert sess.state == ChatState.AWAITING_CLARIFICATION

    r = process_message(sess, "sei lá")
    assert sess.state == ChatState.MENU
    assert "Secretaria" in r["response"]
    assert r["options"] is not None
    assert chatwoot["escalations"] == [], "o bot não escala sozinho — quem decide é o aluno"


# ── 3. Correspondência estrita de menu ────────────────────────────────────────

@pytest.mark.parametrize(
    "entrada",
    ["2026.4", "2026", "3.5", "4.1", "2 mil", "20231604", "1234"],
)
def test_menu_ignora_texto_que_apenas_comeca_com_digito(rag, chatwoot, entrada):
    """A causa raiz: `msg[:1]` transformava qualquer texto iniciado por 2 em escalação."""
    sess = _identified_session()
    r = process_message(sess, entrada)
    assert sess.state == ChatState.MENU
    assert chatwoot["escalations"] == []
    assert "Não entendi" in r["response"] or "não entendi" in r["response"]


@pytest.mark.parametrize(
    "entrada,esperado",
    [
        ("1", "1"),
        ("2", "2"),
        (" 3 ", "3"),
        ("4.", "4"),
        ("1️⃣", "1"),
        ("1 - Fazer uma pergunta", "1"),
        ("1 - Fazer outra pergunta", "1"),
        ("2 - Falar com Secretário", "2"),
        ("3 - Falar com Diretor", "3"),
        ("4 - Encerrar", "4"),
        ("secretaria", "2"),
        ("Diretor", "3"),
        ("encerrar", "4"),
        ("2026.4", None),
        ("3 disciplinas obrigatórias", None),
        ("", None),
        # Ambíguos: "não" pode ser "não, isso não respondeu" — não encerra.
        ("não", None),
        ("obrigado", None),
    ],
)
def test_match_menu_option(entrada, esperado):
    assert cs._match_menu_option(entrada) == esperado


def test_quick_reply_do_chatwoot_escala_normalmente(rag, chatwoot):
    """O payload devolvido pelo botão do widget continua funcionando."""
    sess = _identified_session()
    r = process_message(sess, "2 - Falar com Secretário")
    assert sess.state == ChatState.ESCALATED
    assert len(chatwoot["escalations"]) == 1
    assert r["ticket_id"] == sess.ticket_id


def test_opcao_4_encerra(rag):
    sess = _identified_session()
    process_message(sess, "4")
    assert sess.state == ChatState.ENDED


# ── 4. Refinamentos de atendimento ────────────────────────────────────────────

def test_pergunta_digitada_no_menu_e_respondida(rag, chatwoot):
    """Fallback de texto livre: o aluno não precisa digitar "1" antes de perguntar."""
    sess = _identified_session()
    r = process_message(sess, "Quantas horas de ACC preciso cumprir no curso?")
    assert sess.state in (ChatState.MENU, ChatState.AWAITING_CLARIFICATION)
    assert rag.calls, "a pergunta deveria ter ido para o RAG"
    assert chatwoot["escalations"] == []


def test_pedido_generico_de_humano_pergunta_qual_equipe(rag, chatwoot):
    sess = _identified_session()
    r = process_message(sess, "atendente")
    assert sess.state == ChatState.MENU
    assert chatwoot["escalations"] == [], "não escala sem saber a equipe"
    assert "Secretaria" in r["response"] and "Direção" in r["response"]


def test_comando_menu_sai_do_esclarecimento(rag, chatwoot):
    sess = _identified_session()
    process_message(sess, "1")
    process_message(sess, PERGUNTA)
    assert sess.state == ChatState.AWAITING_CLARIFICATION

    r = process_message(sess, "menu")
    assert sess.state == ChatState.MENU
    assert sess.pending_question is None
    assert r["options"] is not None
    assert chatwoot["escalations"] == []


def test_comando_menu_sai_de_asking_question(rag):
    sess = _identified_session()
    process_message(sess, "1")
    r = process_message(sess, "voltar")
    assert sess.state == ChatState.MENU
    assert not rag.calls, "'voltar' é navegação, não pergunta"


def test_pergunta_com_palavra_de_comando_nao_e_sequestrada(rag):
    """"...sair do curso" contém 'sair', mas é uma pergunta — deve ir ao RAG."""
    sess = _identified_session()
    process_message(sess, "1")
    process_message(sess, "Qual o prazo para sair do curso em 2026.4?")
    assert sess.state != ChatState.ENDED
    assert rag.calls


def test_handoff_leva_a_ultima_pergunta_para_a_equipe(rag, chatwoot):
    """Warm handoff: o atendente recebe o contexto do que já foi perguntado."""
    sess = _identified_session()
    process_message(sess, "1")
    process_message(sess, PERGUNTA)
    process_message(sess, "menu")
    process_message(sess, "2")

    assert sess.state == ChatState.ESCALATED
    contexto = chatwoot["escalations"][0]["context_message"]
    assert sess.ticket_id in contexto
    assert MATRICULA in contexto
    assert EMAIL in contexto
    assert "Última pergunta ao bot" in contexto
    assert "Estágio" in contexto


def test_menu_apos_resposta_oferece_outra_pergunta(rag):
    sess = _identified_session()
    process_message(sess, "1")
    process_message(sess, PERGUNTA)
    r = process_message(sess, PERIODO)
    assert r["options"][0] == "1 - Fazer outra pergunta"


# ── 5. Unidades auxiliares ────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "texto,esperado",
    [
        ("2026.4", "2026.4"),
        ("periodo 2026.1 por favor", "2026.1"),
        ("2026/3", "2026.3"),
        ("2026-2", "2026.2"),
        ("2026", None),
        ("2026.9", None),
        ("não sei", None),
        ("", None),
    ],
)
def test_extract_period(texto, esperado):
    assert cs._extract_period(texto) == esperado


def test_call_rag_propaga_needs_clarification(monkeypatch):
    """O flag do rag_ppc precisa chegar ao fluxo — descartá-lo causou o bug."""

    class _FakeService:
        def ask_question(self, question, session_id=None):
            return {"success": True, "answer": CLARIFICACAO, "needs_clarification": True}

    fake_module = types.ModuleType("backend.infrastructure.rag.rag_ppc")
    fake_module.get_service = lambda: _FakeService()
    monkeypatch.setitem(sys.modules, "backend.infrastructure.rag.rag_ppc", fake_module)

    out = cs._call_rag("qual o prazo?", session_id="s")
    assert out["needs_clarification"] is True
    assert out["answer"] == CLARIFICACAO


def test_call_rag_trata_falha_do_servico(monkeypatch):
    fake_module = types.ModuleType("backend.infrastructure.rag.rag_ppc")

    def _boom():
        raise RuntimeError("ollama fora do ar")

    fake_module.get_service = _boom
    monkeypatch.setitem(sys.modules, "backend.infrastructure.rag.rag_ppc", fake_module)

    out = cs._call_rag("qual o prazo?")
    assert out["needs_clarification"] is False
    assert "indisponível" in out["answer"]


def test_sessao_encerrada_pode_ser_reiniciada():
    from backend.infrastructure.chatbot.chatbot_service import (
        get_or_create_session_by_conversation,
        reset_session_for_conversation,
    )

    sess, novo = get_or_create_session_by_conversation(4242)
    assert novo
    sess.state = ChatState.ENDED

    nova = reset_session_for_conversation(4242)
    assert nova.state == ChatState.AWAITING_MATRICULA
    assert nova.session_id != sess.session_id
    de_novo, criada = get_or_create_session_by_conversation(4242)
    assert not criada and de_novo is nova


# ══════════════════════════════════════════════════════════════════════════════
# Reconhecimento de aluno recorrente
#
# O diretório de contatos é substituído por um dublê em memória: as quatro
# funções que tocam o banco são módulo-level em `chatbot_service` justamente
# para permitir isso sem DATABASE_URL nem Postgres.
# ══════════════════════════════════════════════════════════════════════════════

from datetime import datetime, timedelta  # noqa: E402

TELEFONE = "5591991744186"


class FakeDiretorio:
    """Dublê do diretório de contatos conhecidos (tabela chatbot_contatos_conhecidos)."""

    def __init__(self, registros: dict | None = None):
        self.registros: dict[tuple[str, str], dict] = registros or {}
        self.upserts: list[dict] = []
        self.confirmacoes: list[str] = []
        self.desativacoes: list[tuple[str, str]] = []

    # ── seams de chatbot_service ──
    def buscar(self, session):
        registro = self.registros.get((session.contact_channel, session.contact_key))
        if not registro or not registro.get("ativo", True):
            return None
        if not cs._dentro_da_janela(registro):
            return None
        return dict(registro)

    def registrar(self, session, origem="chatbot"):
        if not session.contact_key:
            return
        self.upserts.append({
            "canal": session.contact_channel, "chave": session.contact_key,
            "matricula": session.matricula, "nome": session.nome,
            "email": session.email, "ticket_id": session.ticket_id, "origem": origem,
        })
        self.registros[(session.contact_channel, session.contact_key)] = {
            "matricula": session.matricula, "nome": session.nome, "email": session.email,
            "ativo": True, "ultimo_atendimento_em": datetime.utcnow(),
        }

    def confirmar(self, session):
        self.confirmacoes.append(session.ticket_id)

    def desativar(self, session):
        if not session.contact_key:
            return
        self.desativacoes.append((session.contact_channel, session.contact_key))
        registro = self.registros.get((session.contact_channel, session.contact_key))
        if registro:
            registro["ativo"] = False


def _registro(nome=NOME, matricula=MATRICULA, email=EMAIL, dias_atras=1, ativo=True):
    return {
        "canal": "whatsapp", "chave": TELEFONE,
        "matricula": matricula, "nome": nome, "email": email,
        "ativo": ativo,
        "ultimo_atendimento_em": datetime.utcnow() - timedelta(days=dias_atras),
    }


@pytest.fixture
def diretorio(monkeypatch) -> FakeDiretorio:
    fake = FakeDiretorio()
    monkeypatch.setattr(cs, "_buscar_contato_conhecido", fake.buscar)
    monkeypatch.setattr(cs, "_registrar_identificacao", fake.registrar)
    monkeypatch.setattr(cs, "_registrar_confirmacao", fake.confirmar)
    monkeypatch.setattr(cs, "_desativar_contato", fake.desativar)
    monkeypatch.setattr(cs, "_espelhar_no_chatwoot", lambda s: None)
    return fake


def _sessao_whatsapp() -> ChatSession:
    sess = ChatSession(session_id="sess-wpp")
    sess.contact_channel = "whatsapp"
    sess.contact_key = TELEFONE
    sess.chatwoot_contact_id = 42
    return sess


# ── Contato desconhecido: nada muda ───────────────────────────────────────────

def test_contato_desconhecido_recebe_boas_vindas_de_sempre(diretorio):
    sess = _sessao_whatsapp()
    abertura = cs.start_session(sess)
    assert abertura["response"] == cs.WELCOME_MESSAGE
    assert abertura["options"] is None
    assert sess.state == ChatState.AWAITING_MATRICULA
    assert abertura["action"] == "boas-vindas enviadas"


def test_sessao_sem_telefone_nunca_tenta_reconhecer(diretorio):
    """Widget do site: comportamento idêntico ao de antes da feature."""
    sess = ChatSession(session_id="sess-web")
    assert cs.start_session(sess)["response"] == cs.WELCOME_MESSAGE
    assert sess.state == ChatState.AWAITING_MATRICULA


# ── Contato conhecido: o fluxo novo ───────────────────────────────────────────

def test_reconhecido_pergunta_confirmacao_com_nome_mascarado(diretorio):
    diretorio.registros[("whatsapp", TELEFONE)] = _registro()
    sess = _sessao_whatsapp()
    abertura = cs.start_session(sess)

    assert sess.state == ChatState.AWAITING_IDENTITY_CONFIRMATION
    assert "Vitor B." in abertura["response"]
    assert abertura["options"] == ["1 - Sim, sou eu", "2 - Não sou eu"]
    # Nada de dado sensível na pergunta feita a quem ainda não provou ser o aluno.
    assert MATRICULA not in abertura["response"]
    assert EMAIL not in abertura["response"]
    assert "Benedito" not in abertura["response"]
    assert "Batista" not in abertura["response"]


def test_confirmar_pula_identificacao_e_gera_ticket_novo(diretorio, rag):
    diretorio.registros[("whatsapp", TELEFONE)] = _registro()
    sess = _sessao_whatsapp()
    cs.start_session(sess)

    r = process_message(sess, "1")

    assert sess.state == ChatState.MENU
    assert sess.matricula == MATRICULA
    assert sess.nome == NOME
    assert sess.email == EMAIL
    assert sess.auto_identified is True
    assert r["ticket_id"].startswith("TKT-")
    assert r["options"] == [
        "1 - Fazer uma pergunta", "2 - Falar com Secretário",
        "3 - Falar com Diretor", "4 - Encerrar",
    ]
    assert diretorio.confirmacoes == [r["ticket_id"]]
    # Saudação usa só o primeiro nome; matrícula e e-mail não são ecoados.
    assert "Vitor" in r["response"]
    assert MATRICULA not in r["response"]
    assert EMAIL not in r["response"]


def test_cada_atendimento_gera_ticket_diferente(diretorio, rag):
    """Requisito explícito: reconhecer não reaproveita o ticket anterior."""
    diretorio.registros[("whatsapp", TELEFONE)] = _registro()

    tickets = []
    for _ in range(2):
        sess = _sessao_whatsapp()
        cs.start_session(sess)
        tickets.append(process_message(sess, "1")["ticket_id"])

    assert tickets[0] != tickets[1]
    assert all(t.startswith("TKT-") for t in tickets)


@pytest.mark.parametrize("resposta", ["1", "sim", "Sim", "1 - Sim, sou eu", "1️⃣", "isso mesmo"])
def test_formas_de_confirmar(diretorio, rag, resposta):
    diretorio.registros[("whatsapp", TELEFONE)] = _registro()
    sess = _sessao_whatsapp()
    cs.start_session(sess)
    process_message(sess, resposta)
    assert sess.state == ChatState.MENU


@pytest.mark.parametrize("resposta", ["2", "nao", "não", "2 - Não sou eu", "outra pessoa"])
def test_negar_cai_no_fluxo_manual_e_desativa_vinculo(diretorio, resposta):
    diretorio.registros[("whatsapp", TELEFONE)] = _registro()
    sess = _sessao_whatsapp()
    cs.start_session(sess)

    r = process_message(sess, resposta)

    assert sess.state == ChatState.AWAITING_MATRICULA
    assert sess.matricula is None and sess.auto_identified is False
    assert "matrícula" in r["response"]
    assert diretorio.desativacoes == [("whatsapp", TELEFONE)]


def test_apos_negar_o_fluxo_classico_completa_normalmente(diretorio, rag):
    diretorio.registros[("whatsapp", TELEFONE)] = _registro(nome="Outra Pessoa Qualquer")
    sess = _sessao_whatsapp()
    cs.start_session(sess)
    process_message(sess, "2")

    process_message(sess, MATRICULA)
    process_message(sess, NOME)
    r = process_message(sess, EMAIL)

    assert sess.state == ChatState.MENU
    assert r["ticket_id"].startswith("TKT-")
    assert sess.auto_identified is False


def test_resposta_incompreensivel_cai_no_manual_sem_lacar(diretorio):
    diretorio.registros[("whatsapp", TELEFONE)] = _registro()
    sess = _sessao_whatsapp()
    cs.start_session(sess)

    for _ in range(cs.MAX_INVALID_ATTEMPTS - 1):
        r = process_message(sess, "sei lá")
        assert sess.state == ChatState.AWAITING_IDENTITY_CONFIRMATION

    r = process_message(sess, "sei lá")
    assert sess.state == ChatState.AWAITING_MATRICULA
    assert "matrícula" in r["response"]


def test_confirmacao_nao_aceita_prefixo(diretorio):
    """Mesma regra estrita do menu: '2026.4' não decide identidade de ninguém."""
    diretorio.registros[("whatsapp", TELEFONE)] = _registro()
    sess = _sessao_whatsapp()
    cs.start_session(sess)
    process_message(sess, "2026.4")
    assert sess.state == ChatState.AWAITING_IDENTITY_CONFIRMATION
    assert diretorio.desativacoes == []


# ── Janela de revalidação e vínculo desativado ────────────────────────────────

def test_vinculo_vencido_nao_e_oferecido(diretorio):
    diretorio.registros[("whatsapp", TELEFONE)] = _registro(
        dias_atras=cs.RECONHECIMENTO_VALIDADE_DIAS + 1
    )
    sess = _sessao_whatsapp()
    assert cs.start_session(sess)["response"] == cs.WELCOME_MESSAGE
    assert sess.state == ChatState.AWAITING_MATRICULA


def test_vinculo_dentro_da_janela_e_oferecido(diretorio):
    diretorio.registros[("whatsapp", TELEFONE)] = _registro(
        dias_atras=cs.RECONHECIMENTO_VALIDADE_DIAS - 1
    )
    sess = _sessao_whatsapp()
    cs.start_session(sess)
    assert sess.state == ChatState.AWAITING_IDENTITY_CONFIRMATION


def test_vinculo_desativado_nao_e_oferecido(diretorio):
    diretorio.registros[("whatsapp", TELEFONE)] = _registro(ativo=False)
    sess = _sessao_whatsapp()
    assert cs.start_session(sess)["response"] == cs.WELCOME_MESSAGE


def test_dentro_da_janela_rejeita_registro_sem_data():
    assert cs._dentro_da_janela({}) is False
    assert cs._dentro_da_janela({"ultimo_atendimento_em": None}) is False
    assert cs._dentro_da_janela({"ultimo_atendimento_em": "2026-01-01"}) is False


# ── Alimentação do diretório ──────────────────────────────────────────────────

def test_identificacao_manual_memoriza_o_contato(diretorio, rag):
    sess = _sessao_whatsapp()
    cs.start_session(sess)
    process_message(sess, MATRICULA)
    process_message(sess, NOME)
    process_message(sess, EMAIL)

    assert len(diretorio.upserts) == 1
    gravado = diretorio.upserts[0]
    assert gravado["canal"] == "whatsapp"
    assert gravado["chave"] == TELEFONE      # forma canônica
    assert gravado["matricula"] == MATRICULA
    assert gravado["nome"] == NOME
    assert gravado["email"] == EMAIL


def test_atendimento_seguinte_ja_reconhece(diretorio, rag):
    """O ciclo completo: primeiro atendimento ensina, segundo reconhece."""
    primeira = _sessao_whatsapp()
    cs.start_session(primeira)
    process_message(primeira, MATRICULA)
    process_message(primeira, NOME)
    process_message(primeira, EMAIL)

    segunda = _sessao_whatsapp()
    abertura = cs.start_session(segunda)
    assert segunda.state == ChatState.AWAITING_IDENTITY_CONFIRMATION
    assert "Vitor B." in abertura["response"]


def test_sessao_sem_telefone_nao_grava_no_diretorio(diretorio, rag):
    sess = ChatSession(session_id="sess-web")
    process_message(sess, MATRICULA)
    process_message(sess, NOME)
    process_message(sess, EMAIL)
    assert diretorio.upserts == []


# ── Degradação: banco fora do ar ──────────────────────────────────────────────

def test_seam_real_engole_falha_do_banco(monkeypatch):
    """A função real tem que devolver None, não propagar — é a garantia de degradação."""
    import sys, types
    fake_repo = types.ModuleType("backend.infrastructure.database.repository")

    def _boom(*a, **k):
        raise RuntimeError("connection refused")

    fake_repo.buscar_chatbot_contato_conhecido = _boom
    monkeypatch.setitem(sys.modules, "backend.infrastructure.database.repository", fake_repo)

    assert cs._buscar_contato_conhecido(_sessao_whatsapp()) is None


def test_seams_de_escrita_engolem_falha(monkeypatch):
    import sys, types
    fake_repo = types.ModuleType("backend.infrastructure.database.repository")

    def _boom(*a, **k):
        raise RuntimeError("disk full")

    fake_repo.upsert_chatbot_contato_conhecido = _boom
    fake_repo.registrar_confirmacao_chatbot_contato = _boom
    fake_repo.desativar_chatbot_contato_conhecido = _boom
    monkeypatch.setitem(sys.modules, "backend.infrastructure.database.repository", fake_repo)

    sess = _sessao_whatsapp()
    sess.matricula, sess.nome, sess.email = MATRICULA, NOME, EMAIL
    cs._registrar_identificacao(sess)     # não deve levantar
    cs._registrar_confirmacao(sess)
    cs._desativar_contato(sess)


# ── LGPD: esquecer meus dados ─────────────────────────────────────────────────

@pytest.mark.parametrize(
    "comando", ["esquecer meus dados", "apagar meus dados", "Excluir meus dados"]
)
def test_esquecer_meus_dados_desativa_vinculo(diretorio, comando):
    diretorio.registros[("whatsapp", TELEFONE)] = _registro()
    sess = _sessao_whatsapp()
    cs.start_session(sess)

    r = process_message(sess, comando)

    assert diretorio.desativacoes == [("whatsapp", TELEFONE)]
    assert sess.state == ChatState.AWAITING_MATRICULA
    assert sess.matricula is None and sess.recognized is None
    assert "não vou mais reconhecer" in r["response"]


def test_esquecer_meus_dados_funciona_tambem_no_menu(diretorio, rag):
    diretorio.registros[("whatsapp", TELEFONE)] = _registro()
    sess = _sessao_whatsapp()
    cs.start_session(sess)
    process_message(sess, "1")
    assert sess.state == ChatState.MENU

    process_message(sess, "esquecer meus dados")
    assert diretorio.desativacoes == [("whatsapp", TELEFONE)]
    assert sess.state == ChatState.AWAITING_MATRICULA


def test_depois_de_esquecer_nao_reconhece_mais(diretorio, rag):
    diretorio.registros[("whatsapp", TELEFONE)] = _registro()
    sess = _sessao_whatsapp()
    cs.start_session(sess)
    process_message(sess, "esquecer meus dados")

    nova = _sessao_whatsapp()
    assert cs.start_session(nova)["response"] == cs.WELCOME_MESSAGE


def test_pergunta_com_a_palavra_esquecer_nao_dispara_o_comando(diretorio, rag):
    """Match exato: uma dúvida que mencione 'dados' não apaga vínculo nenhum."""
    diretorio.registros[("whatsapp", TELEFONE)] = _registro()
    sess = _sessao_whatsapp()
    cs.start_session(sess)
    process_message(sess, "1")
    process_message(sess, "1")
    process_message(sess, "Como faço para apagar meus dados do sistema acadêmico?")
    assert diretorio.desativacoes == []


# ── Handoff: procedência da identificação ─────────────────────────────────────

def test_handoff_diz_que_identificacao_foi_automatica(diretorio, rag, chatwoot):
    diretorio.registros[("whatsapp", TELEFONE)] = _registro()
    sess = _sessao_whatsapp()
    sess.chatwoot_conversation_id = None
    cs.start_session(sess)
    process_message(sess, "1")
    process_message(sess, "2")

    contexto = chatwoot["escalations"][0]["context_message"]
    assert "Identificação: automática" in contexto
    assert "Canal: WhatsApp" in contexto
    # Telefone só aparece mascarado, nunca inteiro.
    assert TELEFONE not in contexto
    assert "*****-4186" in contexto


def test_handoff_diz_que_identificacao_foi_manual(diretorio, rag, chatwoot):
    sess = _sessao_whatsapp()
    sess.chatwoot_conversation_id = None
    cs.start_session(sess)
    process_message(sess, MATRICULA)
    process_message(sess, NOME)
    process_message(sess, EMAIL)
    process_message(sess, "2")

    contexto = chatwoot["escalations"][0]["context_message"]
    assert "Identificação: manual" in contexto


# ── Máscara do nome ───────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "nome,esperado",
    [
        ("Vitor Benedito Ribeiro Batista", "Vitor B."),
        ("Maria Silva", "Maria S."),
        ("Ana", "Ana"),
        ("", "você"),
        ("   ", "você"),
    ],
)
def test_nome_para_exibir(nome, esperado):
    assert cs._nome_para_exibir(nome) == esperado


def test_nome_para_exibir_nunca_revela_sobrenome_completo():
    assert "Benedito" not in cs._nome_para_exibir(NOME)
    assert "Batista" not in cs._nome_para_exibir(NOME)
