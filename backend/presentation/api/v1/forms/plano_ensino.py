from __future__ import annotations

import io
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from typing import Annotated, List

from backend.presentation.schemas.forms import SubmissionResult

router = APIRouter()
MAX_FILE_SIZE = 50 * 1024 * 1024


class _FileLike(io.BytesIO):
    def __init__(self, data: bytes, name: str):
        super().__init__(data)
        self.name = name


@router.post("/plano-ensino", response_model=SubmissionResult, status_code=201)
async def submit_plano_ensino(
    docente: Annotated[str, Form()],
    semestre: Annotated[str, Form()],
    arquivos: Annotated[List[UploadFile], File()] = [],
):
    file_objs: list[_FileLike] = []
    for f in arquivos:
        content = await f.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"Arquivo '{f.filename}' excede 50MB")
        file_objs.append(_FileLike(content, f.filename or "plano.pdf"))

    form_data = {
        "docente": docente,
        "semestre": semestre,
    }

    try:
        from backend.infrastructure.form_service_legacy import process_plano_submission
        result = process_plano_submission(form_data, file_objs)
        drive_links = result.get("drive_links", []) if isinstance(result, dict) else []
        return SubmissionResult(
            id=result.get("id", 0) if isinstance(result, dict) else 0,
            status="recebido",
            message="Plano de ensino enviado com sucesso!",
            drive_links=drive_links,
        )
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Erro ao processar plano de ensino: {e}")
