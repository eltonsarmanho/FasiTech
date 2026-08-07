"""Teste de integração do webhook do Chatwoot (`/chatbot/webhook/chatwoot`).

Sobe o router real em um app FastAPI mínimo e envia payloads `message_created`
como o Chatwoot envia. Só as bordas são substituídas: o RAG e as chamadas HTTP
de saída para o Chatwoot. O que se valida aqui é a fiação — estados, entrega das
mensagens e quick-replies — inclusive o cenário de produção em que responder
"2026.4" a um pedido de esclarecimento escalava o atendimento por engano.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.infrastructure.chatbot import chatbot_service as cs
from backend.infrastructure.chatwoot import chatwoot_service as cw
from backend.presentation.api.v1.chatbot.chatbot_router import router

from tests.test_services.test_chatbot_flow import (
    CLARIFICACAO,
    EMAIL,
    MATRICULA,
    NOME,
    PERGUNTA,
    PERIODO,
    RESPOSTA_FINAL,
    FakeRag,
)

CONVERSATION_ID = 7001
INBOX_ID = 5  # chatwoot_inbox_id_chatweb (default das settings)


@pytest.fixture
def client(monkeypatch):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return TestClient(app)


@pytest.fixture
def outbox(monkeypatch) -> list[dict]:
    """Captura tudo que o bot enviaria ao Chatwoot."""
    sent: list[dict] = []
    monkeypatch.setattr(
        cw, "send_message",
        lambda conv, content, private=False: sent.append(
            {"kind": "note" if private else "text", "conv": conv, "content": content}
        ),
    )
    monkeypatch.setattr(
        cw, "send_quick_replies",
        lambda conv, options, content="Escolha uma opção:": sent.append(
            {"kind": "select", "conv": conv, "content": content, "options": options}
        ),
    )
    monkeypatch.setattr(cw, "assign_team", lambda conv, team: sent.append(
        {"kind": "assign", "conv": conv, "team": team}
    ))
    return sent


@pytest.fixture(autouse=True)
def _isolated_sessions(monkeypatch):
    monkeypatch.setattr(cs, "_sessions_by_conversation", {})
    monkeypatch.setattr(cs, "_sessions", {})


@pytest.fixture
def rag(monkeypatch) -> FakeRag:
    fake = FakeRag()
    monkeypatch.setattr(cs, "_call_rag", fake)
    return fake


def _say(client: TestClient, text: str, *, inbox_id: int = INBOX_ID) -> dict:
    resp = client.post(
        "/api/v1/chatbot/webhook/chatwoot",
        json={
            "event": "message_created",
            "message_type": "incoming",
            "content": text,
            "conversation": {"id": CONVERSATION_ID, "inbox_id": inbox_id},
        },
    )
    assert resp.status_code == 200
    return resp.json()


def _last(outbox: list[dict]) -> dict:
    return outbox[-1]


# ── Cenário relatado, ponta a ponta pelo webhook ──────────────────────────────

def test_conversa_completa_com_esclarecimento(client, outbox, rag):
    # 1ª mensagem: boas-vindas
    assert _say(client, "oi")["action"] == "boas-vindas enviadas"
    assert "matrícula" in _last(outbox)["content"]

    _say(client, MATRICULA)
    _say(client, NOME)
    _say(client, EMAIL)
    ticket_msg = _last(outbox)
    assert "TKT-" in ticket_msg["content"]
    assert ticket_msg["kind"] == "select"  # menu vira botões, em uma bolha só

    # Opção 1 → pergunta
    _say(client, "1 - Fazer uma pergunta")
    out = _say(client, PERGUNTA)
    assert out["state"] == "awaiting_clarification"
    esclarecimento = _last(outbox)
    assert esclarecimento["kind"] == "text", "pedido de esclarecimento não leva menu"
    assert "período letivo" in esclarecimento["content"]

    # ❗ Regressão: "2026.4" é a resposta ao esclarecimento, não a opção 2
    out = _say(client, PERIODO)
    assert out["state"] == "menu"
    assert not any(m["kind"] == "assign" for m in outbox), "não pode ter escalado"
    resposta = _last(outbox)
    assert RESPOSTA_FINAL in resposta["content"]
    assert resposta["kind"] == "select"
    assert resposta["options"][0] == "1 - Fazer outra pergunta"


def test_escalacao_explicita_atribui_equipe_e_manda_nota(client, outbox, rag):
    _say(client, "oi")
    _say(client, MATRICULA)
    _say(client, NOME)
    _say(client, EMAIL)
    out = _say(client, "2")

    assert out["state"] == "escalated"
    assign = [m for m in outbox if m["kind"] == "assign"]
    nota = [m for m in outbox if m["kind"] == "note"]
    assert len(assign) == 1 and assign[0]["conv"] == CONVERSATION_ID
    assert MATRICULA in nota[0]["content"] and EMAIL in nota[0]["content"]

    # Depois de escalar, o bot cala para não atropelar o atendente humano.
    antes = len(outbox)
    assert _say(client, "e aí?")["skipped"] == "sessão em estado escalated"
    assert len(outbox) == antes


def test_atendimento_encerrado_recomeca_em_nova_mensagem(client, outbox, rag):
    _say(client, "oi")
    _say(client, MATRICULA)
    _say(client, NOME)
    _say(client, EMAIL)
    assert _say(client, "4")["state"] == "ended"

    out = _say(client, "olá de novo")
    assert out["action"] == "novo atendimento iniciado"
    assert "matrícula" in _last(outbox)["content"]
    # E o fluxo novo funciona de verdade
    _say(client, MATRICULA)
    assert "nome completo" in _last(outbox)["content"].lower()


def test_fallback_para_texto_puro_quando_canal_nao_aceita_botoes(client, outbox, rag, monkeypatch):
    """WhatsApp em alguns provedores rejeita input_select — a resposta não pode sumir."""
    def _sem_botoes(conv, options, content="Escolha uma opção:"):
        raise RuntimeError("channel does not support input_select")

    monkeypatch.setattr(cw, "send_quick_replies", _sem_botoes)

    _say(client, "oi")
    _say(client, MATRICULA)
    _say(client, NOME)
    _say(client, EMAIL)

    entregue = _last(outbox)
    assert entregue["kind"] == "text"
    assert "TKT-" in entregue["content"]
    assert "1️⃣  Fazer uma pergunta" in entregue["content"], "menu numerado sobrevive em texto"


# ── Guardas do webhook ────────────────────────────────────────────────────────

def test_ignora_eventos_e_canais_fora_do_escopo(client, outbox, rag):
    r = client.post("/api/v1/chatbot/webhook/chatwoot", json={"event": "conversation_updated"})
    assert r.json()["skipped"] == "evento ignorado"

    r = client.post(
        "/api/v1/chatbot/webhook/chatwoot",
        json={"event": "message_created", "message_type": "outgoing", "content": "eco do bot",
              "conversation": {"id": CONVERSATION_ID, "inbox_id": INBOX_ID}},
    )
    assert r.json()["skipped"] == "não é mensagem do visitante"

    assert _say(client, "oi", inbox_id=99)["skipped"].startswith("inbox 99")
    assert outbox == []


# ══════════════════════════════════════════════════════════════════════════════
# Reconhecimento de aluno recorrente, ponta a ponta pelo webhook
# ══════════════════════════════════════════════════════════════════════════════

from datetime import datetime  # noqa: E402

from backend.config.settings import settings  # noqa: E402

from tests.test_services.test_chatbot_flow import (  # noqa: E402
    TELEFONE,
    FakeDiretorio,
    _registro,
)

WHATSAPP_INBOX = settings.chatwoot_inbox_id_whatsapp or 3
# Segredo compartilhado do webhook: sem ele o reconhecimento fica desligado,
# então a configuração "de produção correta" é a linha de base dos testes.
TOKEN = "segredo-do-webhook-123"


@pytest.fixture
def diretorio(monkeypatch) -> FakeDiretorio:
    fake = FakeDiretorio()
    monkeypatch.setattr(cs, "_buscar_contato_conhecido", fake.buscar)
    monkeypatch.setattr(cs, "_registrar_identificacao", fake.registrar)
    monkeypatch.setattr(cs, "_registrar_confirmacao", fake.confirmar)
    monkeypatch.setattr(cs, "_desativar_contato", fake.desativar)
    monkeypatch.setattr(cs, "_espelhar_no_chatwoot", lambda s: None)
    monkeypatch.setattr(settings, "chatwoot_inbox_id_whatsapp", WHATSAPP_INBOX)
    monkeypatch.setattr(settings, "chatwoot_webhook_token", TOKEN)
    return fake


def _say_whatsapp(client: TestClient, text: str, *, telefone: str = "+5591991744186") -> dict:
    """Payload como o Chatwoot envia no inbox de WhatsApp (Channel::Whatsapp)."""
    resp = client.post(
        f"/api/v1/chatbot/webhook/chatwoot?token={TOKEN}",
        json={
            "event": "message_created",
            "message_type": "incoming",
            "content": text,
            "conversation": {"id": CONVERSATION_ID, "inbox_id": WHATSAPP_INBOX},
            "sender": {"id": 42, "name": "Vitor", "phone_number": telefone},
        },
    )
    assert resp.status_code == 200
    return resp.json()


# ── Primeiro contato: ensina o diretório ──────────────────────────────────────

def test_primeiro_atendimento_no_whatsapp_memoriza_o_contato(client, outbox, rag, diretorio):
    assert _say_whatsapp(client, "oi")["action"] == "boas-vindas enviadas"
    assert "matrícula" in _last(outbox)["content"]

    _say_whatsapp(client, MATRICULA)
    _say_whatsapp(client, NOME)
    _say_whatsapp(client, EMAIL)

    assert "TKT-" in _last(outbox)["content"]
    assert len(diretorio.upserts) == 1
    assert diretorio.upserts[0]["chave"] == TELEFONE   # canônico, sem "+" nem máscara


# ── Contato conhecido: o fluxo curto ──────────────────────────────────────────

def test_contato_conhecido_abre_com_confirmacao(client, outbox, rag, diretorio):
    diretorio.registros[("whatsapp", TELEFONE)] = _registro()

    out = _say_whatsapp(client, "oi")

    assert out["action"] == "reconhecimento oferecido"
    abertura = _last(outbox)
    assert abertura["kind"] == "select"
    assert "Vitor B." in abertura["content"]
    assert abertura["options"] == ["1 - Sim, sou eu", "2 - Não sou eu"]
    assert MATRICULA not in abertura["content"]
    assert EMAIL not in abertura["content"]


def test_confirmar_vai_direto_ao_menu_com_ticket_novo(client, outbox, rag, diretorio):
    diretorio.registros[("whatsapp", TELEFONE)] = _registro()
    _say_whatsapp(client, "oi")

    out = _say_whatsapp(client, "1 - Sim, sou eu")

    assert out["state"] == "menu"
    entregue = _last(outbox)
    assert "TKT-" in entregue["content"]
    assert entregue["kind"] == "select"
    assert entregue["options"][0] == "1 - Fazer uma pergunta"
    # Nunca pediu matrícula, nome nem e-mail.
    assert not any("matrícula" in m["content"] for m in outbox if m["kind"] == "text")


def test_negar_volta_para_o_fluxo_completo(client, outbox, rag, diretorio):
    diretorio.registros[("whatsapp", TELEFONE)] = _registro()
    _say_whatsapp(client, "oi")

    _say_whatsapp(client, "2 - Não sou eu")
    assert "matrícula" in _last(outbox)["content"]
    assert diretorio.desativacoes == [("whatsapp", TELEFONE)]

    _say_whatsapp(client, MATRICULA)
    assert "nome completo" in _last(outbox)["content"].lower()


def test_pergunta_apos_reconhecimento_funciona_normalmente(client, outbox, rag, diretorio):
    """O fluxo de perguntas segue idêntico depois do atalho de identificação."""
    diretorio.registros[("whatsapp", TELEFONE)] = _registro()
    _say_whatsapp(client, "oi")
    _say_whatsapp(client, "1")

    _say_whatsapp(client, "1")
    out = _say_whatsapp(client, PERGUNTA)
    assert out["state"] == "awaiting_clarification"

    out = _say_whatsapp(client, PERIODO)
    assert out["state"] == "menu"
    assert RESPOSTA_FINAL in _last(outbox)["content"]
    assert not any(m["kind"] == "assign" for m in outbox)


def test_novo_atendimento_apos_encerrar_reconhece_com_outro_ticket(client, outbox, rag, diretorio):
    diretorio.registros[("whatsapp", TELEFONE)] = _registro()
    _say_whatsapp(client, "oi")
    _say_whatsapp(client, "1")
    primeiro_ticket = _last(outbox)["content"]

    assert _say_whatsapp(client, "4")["state"] == "ended"

    assert _say_whatsapp(client, "oi de novo")["action"] == "novo atendimento iniciado"
    assert "Vitor B." in _last(outbox)["content"], "reconhece de novo no atendimento seguinte"

    _say_whatsapp(client, "1")
    segundo_ticket = _last(outbox)["content"]
    assert primeiro_ticket != segundo_ticket, "cada atendimento tem seu próprio ticket"


def test_fallback_texto_puro_preserva_as_opcoes_de_confirmacao(
    client, outbox, rag, diretorio, monkeypatch
):
    """Se o WhatsApp recusar botões, o texto ainda precisa dizer 1 e 2."""
    def _sem_botoes(conv, options, content="Escolha uma opção:"):
        raise RuntimeError("channel does not support input_select")

    monkeypatch.setattr(cw, "send_quick_replies", _sem_botoes)
    diretorio.registros[("whatsapp", TELEFONE)] = _registro()

    _say_whatsapp(client, "oi")

    entregue = _last(outbox)
    assert entregue["kind"] == "text"
    assert "Vitor B." in entregue["content"]
    assert "1️⃣  Sim, sou eu" in entregue["content"]
    assert "2️⃣  Não sou eu" in entregue["content"]


# ── Segurança ─────────────────────────────────────────────────────────────────

def test_widget_do_site_nao_reconhece_mesmo_com_telefone_forjado(client, outbox, rag, diretorio):
    """
    REGRESSÃO DE SEGURANÇA: no widget o visitante define o próprio contato via
    $chatwoot.setUser. Mesmo mandando o telefone de um aluno cadastrado, tem que
    receber o fluxo manual — nunca o nome dele.
    """
    diretorio.registros[("whatsapp", TELEFONE)] = _registro()

    resp = client.post(
        "/api/v1/chatbot/webhook/chatwoot",
        json={
            "event": "message_created",
            "message_type": "incoming",
            "content": "oi",
            "conversation": {"id": CONVERSATION_ID, "inbox_id": INBOX_ID},  # widget
            "sender": {"id": 99, "name": "Invasor", "phone_number": "+5591991744186"},
        },
    )
    assert resp.status_code == 200
    assert resp.json()["action"] == "boas-vindas enviadas"

    entregue = _last(outbox)
    assert "Vitor" not in entregue["content"]
    assert "matrícula" in entregue["content"]


def test_payload_antigo_sem_sender_continua_funcionando(client, outbox, rag, diretorio):
    """Compatibilidade: o formato que a suíte já usava não pode mudar de comportamento."""
    assert _say(client, "oi")["action"] == "boas-vindas enviadas"
    assert "matrícula" in _last(outbox)["content"]
    _say(client, MATRICULA)
    assert "nome completo" in _last(outbox)["content"].lower()
    assert diretorio.upserts == []


def test_telefone_nunca_aparece_inteiro_no_que_e_enviado(client, outbox, rag, diretorio):
    diretorio.registros[("whatsapp", TELEFONE)] = _registro()
    _say_whatsapp(client, "oi")
    _say_whatsapp(client, "1")
    _say_whatsapp(client, "2")   # escala para a Secretaria

    for msg in outbox:
        assert TELEFONE not in str(msg.get("content", "")), "telefone cru vazou numa mensagem"


# ── Autenticação do webhook ───────────────────────────────────────────────────
#
# O endpoint é público (o Chatwoot precisa alcançá-lo) e o Chatwoot self-hosted
# não assina o payload. Sem o segredo compartilhado, qualquer POST da internet
# poderia alegar o telefone de um aluno e ser reconhecido como ele.

def _say_whatsapp_autenticado(client: TestClient, text: str, *, token: str | None = TOKEN) -> dict:
    url = "/api/v1/chatbot/webhook/chatwoot"
    if token is not None:
        url += f"?token={token}"
    resp = client.post(
        url,
        json={
            "event": "message_created",
            "message_type": "incoming",
            "content": text,
            "conversation": {"id": CONVERSATION_ID, "inbox_id": WHATSAPP_INBOX},
            "sender": {"id": 42, "name": "Vitor", "phone_number": "+5591991744186"},
        },
    )
    assert resp.status_code == 200
    return resp.json()


def test_webhook_autenticado_reconhece(client, outbox, rag, diretorio):
    diretorio.registros[("whatsapp", TELEFONE)] = _registro()
    out = _say_whatsapp_autenticado(client, "oi")
    assert out["action"] == "reconhecimento oferecido"
    assert "Vitor B." in _last(outbox)["content"]


def test_token_pode_vir_no_header(client, outbox, rag, diretorio):
    diretorio.registros[("whatsapp", TELEFONE)] = _registro()
    resp = client.post(
        "/api/v1/chatbot/webhook/chatwoot",
        headers={"X-Webhook-Token": TOKEN},
        json={
            "event": "message_created",
            "message_type": "incoming",
            "content": "oi",
            "conversation": {"id": CONVERSATION_ID, "inbox_id": WHATSAPP_INBOX},
            "sender": {"id": 42, "phone_number": "+5591991744186"},
        },
    )
    assert resp.json()["action"] == "reconhecimento oferecido"


@pytest.mark.parametrize("token", [None, "", "token-errado", "segredo-do-webhook-12"])
def test_payload_forjado_sem_segredo_nao_reconhece(
    client, outbox, rag, diretorio, token
):
    """
    REGRESSÃO DE SEGURANÇA: o endpoint é público. Um POST forjado alegando o
    telefone de um aluno tem que cair no fluxo manual — nunca revelar o nome.
    """
    diretorio.registros[("whatsapp", TELEFONE)] = _registro()

    out = _say_whatsapp_autenticado(client, "oi", token=token)

    assert out["action"] == "boas-vindas enviadas"
    entregue = _last(outbox)
    assert "Vitor" not in entregue["content"]
    assert "matrícula" in entregue["content"]


def test_sem_token_configurado_o_bot_funciona_mas_nao_reconhece(
    client, outbox, rag, diretorio, monkeypatch
):
    """
    Falha segura no deploy: quem subir sem CHATWOOT_WEBHOOK_TOKEN mantém o bot
    de hoje funcionando, só sem o atalho de identificação.
    """
    monkeypatch.setattr(settings, "chatwoot_webhook_token", "")
    diretorio.registros[("whatsapp", TELEFONE)] = _registro()

    out = _say_whatsapp(client, "oi")
    assert out["action"] == "boas-vindas enviadas"

    _say_whatsapp(client, MATRICULA)
    assert "nome completo" in _last(outbox)["content"].lower()


def test_url_exata_configurada_no_chatwoot(client, outbox, rag, diretorio):
    """
    A URL que vai no painel do Chatwoot, na forma exata:
        https://fasitech.cameta.ufpa.br/api/v1/chatbot/webhook/chatwoot?token=<valor>

    O host e o TLS são do nginx; o que importa aqui é caminho + querystring.
    """
    resp = client.post(
        f"/api/v1/chatbot/webhook/chatwoot?token={TOKEN}",
        json={
            "event": "message_created",
            "message_type": "incoming",
            "content": "oi",
            "conversation": {"id": CONVERSATION_ID, "inbox_id": WHATSAPP_INBOX},
            "sender": {"id": 42, "name": "Vitor", "phone_number": "+5591991744186"},
        },
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


@pytest.mark.parametrize(
    "token_forjado",
    ["café", "señor", "токен", "日本語", "tok\x00en", "a" * 5000],
)
def test_token_hostil_nao_derruba_o_webhook(client, outbox, rag, diretorio, token_forjado):
    """
    REGRESSÃO: `secrets.compare_digest` com str levanta TypeError em não-ASCII, e
    a verificação roda antes do try/except do handler — qualquer um poderia
    responder 500 ao Chatwoot e disparar retries.
    """
    resp = client.post(
        "/api/v1/chatbot/webhook/chatwoot",
        params={"token": token_forjado},
        json={
            "event": "message_created",
            "message_type": "incoming",
            "content": "oi",
            "conversation": {"id": CONVERSATION_ID, "inbox_id": WHATSAPP_INBOX},
            "sender": {"id": 42, "phone_number": "+5591991744186"},
        },
    )
    assert resp.status_code == 200, "token hostil não pode virar 500"
    assert resp.json()["action"] == "boas-vindas enviadas"  # e não reconhece


def test_token_com_caractere_nao_ascii_configurado_nao_quebra(
    client, outbox, rag, diretorio, monkeypatch
):
    """Se alguém configurar um segredo com acento, o bot ainda tem que responder."""
    monkeypatch.setattr(settings, "chatwoot_webhook_token", "señor-secreto")
    diretorio.registros[("whatsapp", TELEFONE)] = _registro()
    resp = client.post(
        "/api/v1/chatbot/webhook/chatwoot",
        params={"token": "señor-secreto"},
        json={
            "event": "message_created",
            "message_type": "incoming",
            "content": "oi",
            "conversation": {"id": CONVERSATION_ID, "inbox_id": WHATSAPP_INBOX},
            "sender": {"id": 42, "phone_number": "+5591991744186"},
        },
    )
    assert resp.status_code == 200
    assert resp.json()["action"] == "reconhecimento oferecido"
