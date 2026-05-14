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


@router.post("/projetos", response_model=SubmissionResult, status_code=201)
async def submit_projetos(
    docente: Annotated[str, Form()],
    parecerista1: Annotated[str, Form()],
    parecerista2: Annotated[str, Form()],
    nome_projeto: Annotated[str, Form()],
    carga_horaria: Annotated[str, Form()],
    edital: Annotated[str, Form()],
    natureza: Annotated[str, Form()],
    ano_edital: Annotated[str, Form()],
    solicitacao: Annotated[str, Form()],
    arquivos: Annotated[List[UploadFile], File()] = [],
):
    file_objs: list[_FileLike] = []
    for f in arquivos:
        content = await f.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"Arquivo '{f.filename}' excede 50MB")
        file_objs.append(_FileLike(content, f.filename or "projeto.pdf"))

    form_data = {
        "docente": docente,
        "parecerista1": parecerista1,
        "parecerista2": parecerista2,
        "nome_projeto": nome_projeto,
        "carga_horaria": carga_horaria,
        "edital": edital,
        "natureza": natureza,
        "ano_edital": ano_edital,
        "solicitacao": solicitacao,
    }

    try:
        from backend.infrastructure.form_service_legacy import process_projetos_submission
        result = process_projetos_submission(form_data, file_objs)
        drive_links = result.get("drive_links", []) if isinstance(result, dict) else []
        return SubmissionResult(
            id=result.get("id", 0) if isinstance(result, dict) else 0,
            status="recebido",
            message="Projeto enviado com sucesso!",
            drive_links=drive_links,
        )
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Erro ao processar projeto: {e}")
