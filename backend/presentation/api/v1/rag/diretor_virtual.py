from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, status

from backend.presentation.schemas.forms import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/diretor-virtual/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        from backend.infrastructure.rag.rag_ppc import get_service
        service = get_service()
        result = await asyncio.to_thread(service.ask_question, request.mensagem)
        if not result.get("success"):
            resposta = result.get("message") or result.get("error") or "Não foi possível responder."
        else:
            resposta = result["answer"]
        return ChatResponse(resposta=resposta)
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Diretor Virtual indisponível: {e}")
