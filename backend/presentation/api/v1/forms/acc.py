from __future__ import annotations

import io
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from typing import Annotated

from backend.config.settings import settings
from backend.presentation.schemas.forms import SubmissionResult

router = APIRouter()

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


class _FileLike(io.BytesIO):
    """BytesIO wrapper that carries a filename attribute for legacy compatibility."""
    def __init__(self, data: bytes, name: str):
        super().__init__(data)
        self.name = name


@router.post("/acc", response_model=SubmissionResult, status_code=201)
async def submit_acc(
    nome: Annotated[str, Form()],
    matricula: Annotated[str, Form()],
    email: Annotated[str, Form()],
    turma: Annotated[str, Form()],
    polo: Annotated[str, Form()],
    periodo: Annotated[str, Form()],
    arquivo_pdf: Annotated[UploadFile, File(description="PDF consolidado das ACCs (máx 50MB)")],
):
    content = await arquivo_pdf.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Arquivo excede 50MB")

    form_data = {
        "name": nome,
        "registration": matricula,
        "email": email,
        "class_group": turma,
        "polo": polo,
        "periodo": periodo,
    }
    uploaded_file = _FileLike(content, arquivo_pdf.filename or "acc.pdf")

    try:
        from backend.infrastructure.form_service_legacy import process_acc_submission
        result = process_acc_submission(
            form_data,
            uploaded_file,
            drive_folder_id=settings.acc_folder_id,
            sheet_id=settings.acc_sheet_id,
            notification_recipients=settings.acc_recipients,
        )
        sub_id = result.id if hasattr(result, "id") else (result.get("id", 0) if isinstance(result, dict) else 0)
        link = result.arquivo_pdf_link if hasattr(result, "arquivo_pdf_link") else None
        return SubmissionResult(
            id=sub_id or 0,
            status="recebido",
            message="ACC enviada com sucesso! Você receberá confirmação por e-mail.",
            drive_links=[link] if link else [],
        )
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Erro ao processar ACC: {e}")
