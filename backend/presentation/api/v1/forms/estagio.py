from __future__ import annotations

import io
import logging
import traceback
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from typing import Annotated, List

from backend.presentation.schemas.forms import SubmissionResult

logger = logging.getLogger(__name__)

router = APIRouter()
MAX_FILE_SIZE = 50 * 1024 * 1024


class _FileLike(io.BytesIO):
    def __init__(self, data: bytes, name: str):
        super().__init__(data)
        self.name = name


@router.post("/estagio", response_model=SubmissionResult, status_code=201)
async def submit_estagio(
    nome: Annotated[str, Form()],
    matricula: Annotated[str, Form()],
    email: Annotated[str, Form()],
    turma: Annotated[str, Form()],
    polo: Annotated[str, Form()],
    periodo: Annotated[str, Form()],
    orientador: Annotated[str, Form()],
    titulo: Annotated[str, Form()],
    componente: Annotated[str, Form(description="'Plano de Estágio' ou 'Relatório Final'")],
    arquivos: Annotated[List[UploadFile], File()],
):
    file_objs: list[_FileLike] = []
    for f in arquivos:
        content = await f.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"Arquivo '{f.filename}' excede 50MB")
        file_objs.append(_FileLike(content, f.filename or "file.pdf"))

    form_data = {
        "nome": nome,
        "matricula": matricula,
        "email": email,
        "turma": turma,
        "polo": polo,
        "periodo": periodo,
        "orientador": orientador,
        "titulo": titulo,
        "componente": componente,
    }

    try:
        from backend.infrastructure.form_service_legacy import process_estagio_submission
        result = process_estagio_submission(form_data, file_objs)
        drive_links = result.get("drive_links", []) if isinstance(result, dict) else []
        return SubmissionResult(
            id=result.get("id", 0) if isinstance(result, dict) else 0,
            status="recebido",
            message="Estágio enviado com sucesso! Você receberá confirmação por e-mail.",
            drive_links=drive_links,
        )
    except Exception as e:
        logger.error("Erro ao processar Estágio:\n%s", traceback.format_exc())
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Erro ao processar Estágio: {e}")
