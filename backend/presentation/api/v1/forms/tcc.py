from __future__ import annotations

import io
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from typing import Annotated, List

from backend.config.settings import settings
from backend.presentation.schemas.forms import SubmissionResult

router = APIRouter()
MAX_FILE_SIZE = 50 * 1024 * 1024


class _FileLike(io.BytesIO):
    def __init__(self, data: bytes, name: str):
        super().__init__(data)
        self.name = name


@router.post("/tcc", response_model=SubmissionResult, status_code=201)
async def submit_tcc(
    nome: Annotated[str, Form()],
    matricula: Annotated[str, Form()],
    email: Annotated[str, Form()],
    turma: Annotated[str, Form()],
    polo: Annotated[str, Form()],
    periodo: Annotated[str, Form()],
    orientador: Annotated[str, Form()],
    titulo: Annotated[str, Form()],
    componente: Annotated[str, Form(description="'TCC 1' ou 'TCC 2'")],
    arquivos: Annotated[List[UploadFile], File(description="Arquivos PDF obrigatórios")],
):
    file_objs: list[_FileLike] = []
    for f in arquivos:
        content = await f.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"Arquivo '{f.filename}' excede 50MB")
        file_objs.append(_FileLike(content, f.filename or "file.pdf"))

    if componente == "TCC 2" and len(file_objs) < 2:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "TCC 2 requer no mínimo 2 arquivos: TCC Final + Declaração de Autoria/Termo de Autorização",
        )

    form_data = {
        "name": nome,
        "registration": matricula,
        "email": email,
        "class_group": turma,
        "polo": polo,
        "periodo": periodo,
        "orientador": orientador,
        "titulo": titulo,
        "componente": componente,
    }

    try:
        from backend.infrastructure.form_service_legacy import process_tcc_submission
        result = process_tcc_submission(
            form_data,
            file_objs,
            drive_folder_id=settings.tcc_folder_id,
            sheet_id=settings.tcc_sheet_id,
            notification_recipients=settings.tcc_recipients,
        )
        drive_links = result.get("drive_links", []) if isinstance(result, dict) else []
        sub_id = result.get("id", 0) if isinstance(result, dict) else 0
        return SubmissionResult(
            id=sub_id,
            status="recebido",
            message=f"{componente} enviado com sucesso! Você receberá confirmação por e-mail.",
            drive_links=drive_links,
        )
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Erro ao processar TCC: {e}")
