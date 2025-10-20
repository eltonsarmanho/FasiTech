from __future__ import annotations

from fastapi import APIRouter

from src.models.schemas import Submission

router = APIRouter()


@router.post("/submit")
async def submit_form(payload: Submission) -> dict[str, str]:
    """Recebe dados do formulário e retorna confirmação."""
    # TODO: chamar serviços de processamento, Drive e Sheets
    _ = payload
    return {"detail": "Formulário recebido"}
