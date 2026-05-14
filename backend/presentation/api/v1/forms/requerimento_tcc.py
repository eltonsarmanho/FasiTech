from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from backend.presentation.schemas.forms import RequerimentoTccFormRequest, SubmissionResult

router = APIRouter()


@router.post("/requerimento-tcc", response_model=SubmissionResult, status_code=201)
async def submit_requerimento_tcc(data: RequerimentoTccFormRequest):
    try:
        from backend.infrastructure.form_service_legacy import process_requerimento_tcc_submission
        result = process_requerimento_tcc_submission(**data.model_dump())
        return SubmissionResult(
            id=result.get("id", 0),
            status="recebido",
            message="Requerimento de TCC registrado com sucesso!",
        )
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Erro ao registrar requerimento: {e}")
