"""
Extração da identidade do contato a partir do webhook do Chatwoot.

O payload de `message_created` carrega quem está falando, mas a posição do dado
varia com a versão do Chatwoot e com o tipo de canal. Em vez de apostar em um
caminho só, tentamos vários em ordem e registramos qual funcionou — é o log que
permite descobrir, com tráfego real, o formato da instância em produção.

Nada aqui levanta exceção: contato não identificado é um resultado válido (o
chatbot simplesmente segue pedindo matrícula, nome e e-mail como sempre fez).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

from backend.utils.phone import mascarar_telefone, normalizar_telefone

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ContatoChatwoot:
    """Identidade extraída do payload. Todos os campos podem ser None."""

    canal: Optional[str] = None       # "whatsapp" | "email" | None
    chave: Optional[str] = None       # telefone canônico OU e-mail minúsculo
    telefone: Optional[str] = None    # canônico ("5591991744186")
    email: Optional[str] = None
    nome: Optional[str] = None        # nome de perfil — só telemetria, ver abaixo
    contact_id: Optional[int] = None
    origem: str = "nenhuma"           # qual caminho do payload funcionou

    @property
    def identificado(self) -> bool:
        return bool(self.canal and self.chave)


def _dict(valor: Any) -> dict:
    """Coerção defensiva: o Chatwoot às vezes manda `null` onde esperamos objeto."""
    return valor if isinstance(valor, dict) else {}


def _texto(valor: Any) -> Optional[str]:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def extrair_contato(
    payload: dict,
    *,
    inbox_id: Optional[int] = None,
    whatsapp_inbox_id: Optional[int] = None,
) -> ContatoChatwoot:
    """
    Lê a identidade do contato do payload do webhook.

    ⚠️ SEGURANÇA — só devolve chave de reconhecimento quando a mensagem vem do
    inbox do WhatsApp (`inbox_id == whatsapp_inbox_id`, ambos truthy).

    O motivo: no widget do site, o próprio visitante consegue definir
    `phone_number`, `email` e `identifier` do contato chamando
    `window.$chatwoot.setUser(...)` pelo console do navegador. Aceitar telefone
    vindo dali deixaria qualquer pessoa se passar pelo telefone de um aluno e
    receber o nome dele — e, ao confirmar, abrir ticket e falar com a Secretaria
    em nome dele. No `Channel::Whatsapp` o telefone é atestado pelo próprio
    canal e não é editável pelo remetente.

    Falha fechada: se `whatsapp_inbox_id` não estiver configurado (default 0 em
    settings), nenhum reconhecimento acontece e o fluxo manual roda.

    Ordem de tentativa para o telefone (a primeira que normalizar vence):
      1. sender.phone_number
      2. conversation.meta.sender.phone_number
      3. conversation.contact_inbox.source_id   (é o `wa_id` no Channel::Whatsapp)
      4. sender.identifier

    Um candidato que não normaliza é descartado e passamos ao próximo — assim um
    `source_id` de widget do site ("web-widget-abc123") é corretamente ignorado
    em vez de virar uma chave inválida.
    """
    payload = _dict(payload)
    conversation = _dict(payload.get("conversation"))
    sender = _dict(payload.get("sender"))
    meta_sender = _dict(_dict(conversation.get("meta")).get("sender"))
    contact_inbox = _dict(conversation.get("contact_inbox"))

    # Coerção tolerante: um inbox_id não numérico não pode derrubar o webhook —
    # falha fechada (sem reconhecimento), que é o lado seguro do erro.
    try:
        canal_confiavel = bool(
            inbox_id and whatsapp_inbox_id and int(inbox_id) == int(whatsapp_inbox_id)
        )
    except (TypeError, ValueError):
        canal_confiavel = False

    telefone: Optional[str] = None
    origem = "nenhuma"

    if canal_confiavel:
        candidatos = [
            ("sender.phone_number", sender.get("phone_number")),
            ("meta.sender.phone_number", meta_sender.get("phone_number")),
            ("contact_inbox.source_id", contact_inbox.get("source_id")),
            ("sender.identifier", sender.get("identifier")),
        ]
        for rotulo, bruto in candidatos:
            normalizado = normalizar_telefone(bruto)
            if normalizado:
                telefone, origem = normalizado, rotulo
                break

    email = _texto(sender.get("email")) or _texto(meta_sender.get("email"))
    if email:
        email = email.lower()

    contact_id = sender.get("id") or meta_sender.get("id")
    try:
        contact_id = int(contact_id) if contact_id is not None else None
    except (TypeError, ValueError):
        contact_id = None

    # O nome de perfil do WhatsApp é editável pelo usuário e não é o nome do
    # SIGAA. Fica aqui para telemetria; NUNCA preenche session.nome.
    nome = _texto(sender.get("name")) or _texto(meta_sender.get("name"))

    # O e-mail NÃO vira chave de reconhecimento. No widget do site ele é digitado
    # pelo próprio visitante no formulário de pré-chat, sem nenhuma verificação:
    # bastaria digitar o e-mail de um aluno para ser reconhecido como ele. Fica
    # capturado só para telemetria até existir um canal que o comprove.
    if telefone:
        canal, chave = "whatsapp", telefone
    else:
        canal, chave = None, None

    contato = ContatoChatwoot(
        canal=canal,
        chave=chave,
        telefone=telefone,
        email=email,
        nome=nome,
        contact_id=contact_id,
        origem=origem,
    )

    if contato.identificado:
        logger.info(
            "Chatwoot: contato extraído via %s (canal=%s chave=%s contact_id=%s)",
            contato.origem,
            contato.canal,
            mascarar_telefone(telefone) if telefone else "<email>",
            contact_id,
        )
    elif canal_confiavel:
        # Diagnóstico para descobrir o formato real do payload em produção sem
        # despejar dados pessoais no log (só os NOMES dos campos).
        logger.info(
            "Chatwoot: sem telefone no payload do WhatsApp (chaves=%s conversation=%s sender=%s)",
            sorted(payload.keys()),
            sorted(conversation.keys()),
            sorted(sender.keys()),
        )

    return contato
