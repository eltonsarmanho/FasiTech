"""
Router do chatbot geral — Diretor Virtual com fluxo de ticket.

Endpoint genérico (microserviço) consumível pelo frontend web e por integrações WhatsApp.

POST /api/v1/chatbot/message
  Corpo: { "session_id": "uuid-ou-null", "message": "texto do usuário" }
  Resposta: { "session_id", "response", "options", "ticket_id", "state" }

GET /api/v1/chatbot/health
  Retorna status do serviço.
"""
from __future__ import annotations

import asyncio
import logging
import secrets

from fastapi import APIRouter, HTTPException, Request, status

from backend.infrastructure.chatbot.chatbot_service import WELCOME_MESSAGE
from backend.presentation.schemas.forms import ChatbotRequest, ChatbotResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# WELCOME_MESSAGE vive em chatbot_service (junto do resto do texto do fluxo) e é
# reexportado aqui porque os endpoints REST e os testes o importam deste módulo.
__all__ = ["router", "WELCOME_MESSAGE"]


@router.post("/chatbot/message", response_model=ChatbotResponse, summary="Enviar mensagem ao chatbot")
async def chatbot_message(req: ChatbotRequest) -> ChatbotResponse:
    """
    Processa uma mensagem do usuário e retorna a resposta do bot com o estado da conversa.
    Se `session_id` for nulo ou inválido, uma nova sessão é criada automaticamente.
    """
    try:
        from backend.infrastructure.chatbot.chatbot_service import (
            get_or_create_session,
            process_message,
        )

        session = get_or_create_session(req.session_id)

        # Primeira mensagem (sessão nova): ignorar o texto e enviar boas-vindas
        if req.session_id != session.session_id:
            return ChatbotResponse(
                session_id=session.session_id,
                response=WELCOME_MESSAGE,
                options=None,
                ticket_id=None,
                state=session.state.value,
            )

        result = await asyncio.to_thread(process_message, session, req.message)

        return ChatbotResponse(
            session_id=session.session_id,
            response=result["response"],
            options=result.get("options"),
            ticket_id=result.get("ticket_id"),
            state=result["state"].value if hasattr(result["state"], "value") else result["state"],
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no chatbot: {exc}",
        )


@router.post("/chatbot/start", response_model=ChatbotResponse, summary="Iniciar nova sessão do chatbot")
async def chatbot_start() -> ChatbotResponse:
    """Cria uma nova sessão e retorna a mensagem de boas-vindas com o session_id."""
    try:
        from backend.infrastructure.chatbot.chatbot_service import get_or_create_session

        session = get_or_create_session(None)
        return ChatbotResponse(
            session_id=session.session_id,
            response=WELCOME_MESSAGE,
            options=None,
            ticket_id=None,
            state=session.state.value,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao iniciar sessão: {exc}",
        )


@router.get("/chatbot/health", summary="Status do chatbot")
async def chatbot_health() -> dict:
    return {"status": "ok", "service": "Diretor Virtual Chatbot"}


@router.get("/chatbot/chatwoot-check", summary="Diagnóstico da conexão com o Chatwoot")
async def chatwoot_check() -> dict:
    """
    Testa a conectividade com o Chatwoot e lista inboxes/equipes disponíveis.
    Use para validar token, URL e IDs de equipes antes de colocar em produção.
    """
    from backend.infrastructure.chatwoot.chatwoot_service import check_connection
    return check_connection()


def _deliver(conversation_id: int, text: str, options: list[str] | None) -> None:
    """
    Entrega a resposta do bot na conversa do Chatwoot.

    Com opções, tenta uma única mensagem `input_select` que já traz o texto e os
    botões (evita a bolha extra só com "Escolha uma opção:"). Se o canal não
    aceitar botões — o WhatsApp varia conforme o provedor —, cai para texto puro,
    que continua legível porque a resposta já embute o menu numerado.
    """
    from backend.infrastructure.chatwoot.chatwoot_service import send_message, send_quick_replies

    if options:
        try:
            send_quick_replies(conversation_id, options, content=text)
            return
        except Exception as exc:
            logger.warning(
                "Chatwoot: quick-replies indisponíveis na conversa %s (%s) — enviando texto puro",
                conversation_id, exc,
            )

    send_message(conversation_id, text)


def _webhook_autenticado(request: Request) -> bool:
    """
    Confere o segredo compartilhado do webhook.

    O endpoint é público (o Chatwoot precisa alcançá-lo) e o Chatwoot self-hosted
    não assina o payload. O segredo vai na querystring da URL configurada lá —
    é o que distingue um POST do Chatwoot de um POST forjado por qualquer um na
    internet, que poderia alegar o telefone de um aluno e se passar por ele.

    Sem `CHATWOOT_WEBHOOK_TOKEN` configurado devolve False: o bot continua
    funcionando como antes, mas sem reconhecimento de contato.
    """
    from backend.config.settings import settings

    esperado = settings.chatwoot_webhook_token
    if not esperado:
        return False
    recebido = (
        request.query_params.get("token")
        or request.headers.get("x-webhook-token")
        or ""
    )
    # Comparação em bytes: `compare_digest` com str levanta TypeError quando há
    # caractere não-ASCII, e um `?token=café` de qualquer origem derrubaria o
    # webhook. Em bytes o tempo de comparação continua constante.
    return secrets.compare_digest(recebido.encode("utf-8"), esperado.encode("utf-8"))


@router.post("/chatbot/webhook/chatwoot", summary="Webhook do Chatwoot — roda o fluxo do bot dentro da conversa")
async def chatwoot_webhook(request: Request) -> dict:
    """
    Configurar em: Chatwoot → Configurações → Integrações → Webhooks
    URL: https://fasitech.cameta.ufpa.br/api/v1/chatbot/webhook/chatwoot?token=<CHATWOOT_WEBHOOK_TOKEN>
    Evento necessário: apenas "Mensagem criada (message_created)".

    O `token` é obrigatório para que o reconhecimento de contato por telefone
    seja ativado — ver `_webhook_autenticado`.

    Sempre responde 200 (mesmo em erro interno) para não disparar retries
    agressivos do Chatwoot — falhas são apenas logadas.
    """
    autenticado = _webhook_autenticado(request)

    try:
        payload = await request.json()
    except Exception:
        return {"ok": False, "error": "payload inválido"}

    if payload.get("event") != "message_created":
        return {"ok": True, "skipped": "evento ignorado"}

    # Só reage a mensagens do visitante — evita loop com as respostas que o
    # próprio bot envia (essas chegam como message_type "outgoing").
    if payload.get("message_type") != "incoming":
        return {"ok": True, "skipped": "não é mensagem do visitante"}

    conversation = payload.get("conversation") or {}
    conversation_id = conversation.get("id") or payload.get("conversation_id")
    content = (payload.get("content") or "").strip()

    if not conversation_id:
        return {"ok": False, "error": "conversation_id ausente no payload"}

    try:
        from backend.config.settings import settings
        from backend.infrastructure.chatbot.chatbot_service import (
            ChatState,
            get_or_create_session_by_conversation,
            process_message,
            reset_session_for_conversation,
            start_session,
        )
        from backend.infrastructure.chatwoot.chatwoot_payload import extrair_contato

        # Só roda o bot nos inboxes configurados (site + WhatsApp) — outros canais
        # (ex.: e-mail) na mesma conta ficam de fora.
        inbox_id = conversation.get("inbox_id") or payload.get("inbox", {}).get("id")
        if inbox_id and inbox_id not in settings.chatwoot_bot_inbox_ids:
            return {"ok": True, "skipped": f"inbox {inbox_id} não é um inbox do chatbot"}

        session, is_new = get_or_create_session_by_conversation(int(conversation_id))

        # Identidade do canal (no WhatsApp, o telefone). Leitura pura de dict,
        # feita em toda mensagem porque nem todo payload traz os mesmos campos —
        # a primeira que trouxer carimba a sessão.
        # Duas condições, ambas necessárias:
        #  • o inbox é o do WhatsApp — só lá o telefone é atestado pelo canal
        #    (no widget do site o visitante define os próprios dados);
        #  • o webhook veio autenticado — sem o segredo, qualquer POST da
        #    internet poderia alegar o telefone de um aluno.
        contato = extrair_contato(
            payload,
            inbox_id=inbox_id,
            whatsapp_inbox_id=(
                settings.chatwoot_inbox_id_whatsapp if autenticado else None
            ),
        )
        if contato.identificado:
            session.contact_channel = contato.canal
            session.contact_key = contato.chave
        if contato.contact_id:
            session.chatwoot_contact_id = contato.contact_id

        # Conversa já encaminhada para um humano: bot fica em silêncio para não
        # atropelar o atendimento da equipe.
        if session.state == ChatState.ESCALATED:
            return {"ok": True, "skipped": f"sessão em estado {session.state.value}"}

        # Atendimento encerrado pelo próprio aluno (opção 4): uma nova mensagem
        # significa um novo atendimento — recomeça em vez de ficar mudo até o TTL.
        # Passa pelo reconhecimento de novo, e o ticket gerado será outro.
        if session.state == ChatState.ENDED:
            session = reset_session_for_conversation(int(conversation_id))
            session.welcomed = True
            abertura = await asyncio.to_thread(start_session, session)
            await asyncio.to_thread(
                _deliver, int(conversation_id), abertura["response"], abertura.get("options"),
            )
            return {"ok": True, "action": "novo atendimento iniciado"}

        if is_new or not session.welcomed:
            session.welcomed = True
            abertura = await asyncio.to_thread(start_session, session)
            await asyncio.to_thread(
                _deliver, int(conversation_id), abertura["response"], abertura.get("options"),
            )
            return {"ok": True, "action": abertura["action"]}

        result = await asyncio.to_thread(process_message, session, content)

        await asyncio.to_thread(
            _deliver, int(conversation_id), result["response"], result.get("options"),
        )

        return {"ok": True, "state": result["state"].value if hasattr(result["state"], "value") else result["state"]}
    except Exception as exc:
        logger.error("Erro no webhook do Chatwoot (conversation_id=%s): %s", conversation_id, exc, exc_info=True)
        return {"ok": False, "error": str(exc)}
