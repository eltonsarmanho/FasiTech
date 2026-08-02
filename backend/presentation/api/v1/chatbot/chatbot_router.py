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

from fastapi import APIRouter, HTTPException, Request, status

from backend.presentation.schemas.forms import ChatbotRequest, ChatbotResponse

logger = logging.getLogger(__name__)

router = APIRouter()

WELCOME_MESSAGE = (
    "Olá! Sou o Diretor Virtual da FASI 🤖\n\n"
    "Posso ajudá-lo com dúvidas sobre matrículas, TCC, ACC, estágio, PPC e normas do curso.\n\n"
    "Para começar, diga sua **matrícula**:"
)


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


@router.post("/chatbot/webhook/chatwoot", summary="Webhook do Chatwoot — roda o fluxo do bot dentro da conversa")
async def chatwoot_webhook(request: Request) -> dict:
    """
    Configurar em: Chatwoot → Configurações → Integrações → Webhooks
    URL: https://fasitech.cameta.ufpa.br/api/v1/chatbot/webhook/chatwoot
    Evento necessário: apenas "Mensagem criada (message_created)".

    Sempre responde 200 (mesmo em erro interno) para não disparar retries
    agressivos do Chatwoot — falhas são apenas logadas.
    """
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
        )
        from backend.infrastructure.chatwoot.chatwoot_service import send_message, send_quick_replies

        # Inbox diferente da do widget web (ex.: outro canal na mesma conta) — ignora.
        inbox_id = conversation.get("inbox_id") or payload.get("inbox", {}).get("id")
        if inbox_id and settings.chatwoot_inbox_id_chatweb and inbox_id != settings.chatwoot_inbox_id_chatweb:
            return {"ok": True, "skipped": f"inbox {inbox_id} não é o inbox do chatbot"}

        session, is_new = get_or_create_session_by_conversation(int(conversation_id))

        # Conversa já encaminhada para humano ou encerrada: bot fica em silêncio.
        if session.state in (ChatState.ESCALATED, ChatState.ENDED):
            return {"ok": True, "skipped": f"sessão em estado {session.state.value}"}

        if is_new or not session.welcomed:
            session.welcomed = True
            await asyncio.to_thread(
                send_message, int(conversation_id), WELCOME_MESSAGE,
            )
            return {"ok": True, "action": "boas-vindas enviadas"}

        result = await asyncio.to_thread(process_message, session, content)

        await asyncio.to_thread(send_message, int(conversation_id), result["response"])
        if result.get("options"):
            await asyncio.to_thread(send_quick_replies, int(conversation_id), result["options"])

        return {"ok": True, "state": result["state"].value if hasattr(result["state"], "value") else result["state"]}
    except Exception as exc:
        logger.error("Erro no webhook do Chatwoot (conversation_id=%s): %s", conversation_id, exc, exc_info=True)
        return {"ok": False, "error": str(exc)}
