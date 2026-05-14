from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from backend.presentation.schemas.forms import SocialFormRequest, SubmissionResult

router = APIRouter()


@router.post("/social", response_model=SubmissionResult, status_code=201)
async def submit_social(data: SocialFormRequest):
    try:
        from backend.infrastructure.form_service_legacy import process_social_submission
        result = process_social_submission(**data.model_dump())
        return SubmissionResult(
            id=result.get("id", 0),
            status="recebido",
            message="Formulário social enviado com sucesso! Obrigado pela participação.",
        )
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Erro ao salvar dados sociais: {e}")
