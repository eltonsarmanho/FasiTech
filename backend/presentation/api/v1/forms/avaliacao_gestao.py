from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from backend.presentation.schemas.forms import AvaliacaoGestaoFormRequest, SubmissionResult

router = APIRouter()


@router.post("/avaliacao-gestao", response_model=SubmissionResult, status_code=201)
async def submit_avaliacao_gestao(data: AvaliacaoGestaoFormRequest):
    try:
        from backend.infrastructure.form_service_legacy import process_avaliacao_gestao_submission
        result = process_avaliacao_gestao_submission(**data.model_dump())
        return SubmissionResult(
            id=result.get("id", 0),
            status="recebido",
            message="Avaliação registrada com sucesso! Obrigado pelo feedback.",
        )
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Erro ao registrar avaliação: {e}")
