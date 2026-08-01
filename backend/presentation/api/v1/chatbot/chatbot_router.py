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

from fastapi import APIRouter, HTTPException, status

from backend.presentation.schemas.forms import ChatbotRequest, ChatbotResponse

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
