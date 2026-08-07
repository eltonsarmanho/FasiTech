"""Testes de extração da identidade do contato no webhook do Chatwoot.

O foco aqui é SEGURANÇA. Reconhecer um aluno pelo telefone só é aceitável se o
telefone for atestado pelo canal. No widget do site o próprio visitante define
`phone_number`, `email` e `identifier` do contato — basta chamar
`window.$chatwoot.setUser(...)` no console do navegador. Se aceitássemos aquele
telefone, qualquer pessoa se passaria por um aluno: receberia o nome dele e, ao
confirmar, abriria ticket e falaria com a Secretaria em nome dele.

Por isso a extração só devolve chave quando `inbox_id == whatsapp_inbox_id`.
"""
from __future__ import annotations

import pytest

from backend.infrastructure.chatwoot.chatwoot_payload import extrair_contato

WHATSAPP_INBOX = 3
WIDGET_INBOX = 5
TELEFONE = "5591991744186"


def _payload(**overrides) -> dict:
    base = {
        "event": "message_created",
        "message_type": "incoming",
        "content": "oi",
        "conversation": {"id": 1, "inbox_id": WHATSAPP_INBOX},
        "sender": {"id": 42, "name": "Vitor", "phone_number": "+5591991744186"},
    }
    base.update(overrides)
    return base


def _extrair(payload: dict, inbox_id: int = WHATSAPP_INBOX):
    return extrair_contato(
        payload, inbox_id=inbox_id, whatsapp_inbox_id=WHATSAPP_INBOX
    )


# ── Caminho feliz ─────────────────────────────────────────────────────────────

def test_extrai_telefone_do_sender():
    c = _extrair(_payload())
    assert c.identificado
    assert c.canal == "whatsapp"
    assert c.chave == TELEFONE
    assert c.contact_id == 42
    assert c.origem == "sender.phone_number"


@pytest.mark.parametrize(
    "payload_extra,origem_esperada",
    [
        (
            {"sender": {"id": 7},
             "conversation": {"id": 1, "inbox_id": WHATSAPP_INBOX,
                              "meta": {"sender": {"id": 7, "phone_number": "+5591991744186"}}}},
            "meta.sender.phone_number",
        ),
        (
            {"sender": {"id": 7},
             "conversation": {"id": 1, "inbox_id": WHATSAPP_INBOX,
                              "contact_inbox": {"source_id": "5591991744186"}}},
            "contact_inbox.source_id",
        ),
        (
            {"sender": {"id": 7, "identifier": "+55 91 99174-4186"},
             "conversation": {"id": 1, "inbox_id": WHATSAPP_INBOX}},
            "sender.identifier",
        ),
    ],
)
def test_fallbacks_em_ordem(payload_extra, origem_esperada):
    """Cada caminho alternativo funciona e se identifica no campo `origem`."""
    c = _extrair(_payload(**payload_extra))
    assert c.chave == TELEFONE
    assert c.origem == origem_esperada


def test_precedencia_o_primeiro_caminho_vence():
    c = _extrair(_payload(
        sender={"id": 1, "phone_number": "+5591991744186", "identifier": "5511987654321"},
    ))
    assert c.chave == TELEFONE
    assert c.origem == "sender.phone_number"


# ── Segurança ─────────────────────────────────────────────────────────────────

def test_widget_do_site_nao_produz_chave_mesmo_com_telefone_no_payload():
    """
    REGRESSÃO DE SEGURANÇA: um visitante do site pode definir o próprio
    phone_number via $chatwoot.setUser. Aceitar isso seria personificação.
    """
    c = _extrair(
        _payload(conversation={"id": 1, "inbox_id": WIDGET_INBOX}),
        inbox_id=WIDGET_INBOX,
    )
    assert not c.identificado
    assert c.canal is None and c.chave is None
    assert c.telefone is None


def test_identifier_forjado_no_widget_e_ignorado():
    """O `identifier` é texto livre gravável pelo cliente — não vale em outro canal."""
    c = _extrair(
        _payload(
            sender={"id": 9, "identifier": "+5591991744186"},
            conversation={"id": 1, "inbox_id": WIDGET_INBOX},
        ),
        inbox_id=WIDGET_INBOX,
    )
    assert not c.identificado


def test_email_nunca_vira_chave_de_reconhecimento():
    """
    REGRESSÃO DE SEGURANÇA: o e-mail do pré-chat é digitado pelo visitante e
    não é verificado. Se virasse chave, bastaria digitar o e-mail de um aluno
    para ser reconhecido como ele.
    """
    c = _extrair(_payload(
        sender={"id": 3, "email": "vitor.batista@cameta.ufpa.br"},
        conversation={"id": 1, "inbox_id": WHATSAPP_INBOX},
    ))
    assert c.email == "vitor.batista@cameta.ufpa.br"  # capturado para telemetria
    assert c.canal != "email"
    assert not c.identificado                          # mas nunca é chave


def test_falha_fechada_quando_inbox_do_whatsapp_nao_esta_configurado():
    """`chatwoot_inbox_id_whatsapp` tem default 0 — sem config, sem reconhecimento."""
    c = extrair_contato(_payload(), inbox_id=WHATSAPP_INBOX, whatsapp_inbox_id=0)
    assert not c.identificado


def test_sem_inbox_no_payload_nao_reconhece():
    c = extrair_contato(_payload(), inbox_id=None, whatsapp_inbox_id=WHATSAPP_INBOX)
    assert not c.identificado


def test_nome_de_perfil_nunca_seria_confundido_com_identidade():
    """
    O nome do WhatsApp é editável pelo usuário. Fica disponível para log, mas o
    fluxo não tem caminho que o use como nome do aluno.
    """
    c = _extrair(_payload(sender={"id": 1, "name": "Reitor da UFPA 👑",
                                  "phone_number": "+5591991744186"}))
    assert c.nome == "Reitor da UFPA 👑"
    assert c.chave == TELEFONE  # a identidade vem do telefone, não do nome


# ── Robustez ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"conversation": None, "sender": None},
        {"sender": {"phone_number": None}, "conversation": {"inbox_id": WHATSAPP_INBOX}},
        {"sender": {"phone_number": "não é telefone"}, "conversation": {"inbox_id": WHATSAPP_INBOX}},
        {"sender": "string em vez de objeto", "conversation": {"inbox_id": WHATSAPP_INBOX}},
        {"sender": {"id": "abc", "phone_number": "+5591991744186"},
         "conversation": {"inbox_id": WHATSAPP_INBOX}},
    ],
)
def test_payload_degenerado_nunca_levanta(payload):
    c = _extrair(payload)
    assert c is not None  # o pior resultado aceitável é "não identificado"


def test_source_id_de_widget_nao_normaliza_e_e_descartado():
    c = _extrair(_payload(
        sender={"id": 1},
        conversation={"id": 1, "inbox_id": WHATSAPP_INBOX,
                      "contact_inbox": {"source_id": "web-widget-abc123"}},
    ))
    assert not c.identificado


def test_contact_id_invalido_nao_quebra():
    c = _extrair(_payload(sender={"id": "xyz", "phone_number": "+5591991744186"}))
    assert c.contact_id is None
    assert c.chave == TELEFONE


@pytest.mark.parametrize("inbox_id", ["abc", {}, [], object()])
def test_inbox_id_nao_numerico_falha_fechado(inbox_id):
    """Um inbox_id inesperado não pode derrubar o webhook — só desliga o reconhecimento."""
    c = extrair_contato(_payload(), inbox_id=inbox_id, whatsapp_inbox_id=WHATSAPP_INBOX)
    assert not c.identificado


def test_inbox_id_como_string_numerica_ainda_reconhece():
    c = extrair_contato(_payload(), inbox_id=str(WHATSAPP_INBOX), whatsapp_inbox_id=WHATSAPP_INBOX)
    assert c.chave == TELEFONE
