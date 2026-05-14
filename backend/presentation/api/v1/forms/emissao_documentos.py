from __future__ import annotations

import asyncio
import io
import logging
import traceback
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from typing import Annotated

from backend.config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()
MAX_FILE_SIZE = 50 * 1024 * 1024

DOCUMENT_TYPE_MAP = {
    "conclusao": "Comprovante de Conclusão de Curso",
    "matricula_ativa": "Comprovante de Matrícula Ativa",
    "Comprovante de Conclusão de Curso": "Comprovante de Conclusão de Curso",
    "Comprovante de Matrícula Ativa": "Comprovante de Matrícula Ativa",
}


class _FileLike(io.BytesIO):
    def __init__(self, data: bytes, name: str):
        super().__init__(data)
        self.name = name
        self.type = "application/pdf"


@router.post("/emissao-documentos", status_code=200)
async def submit_emissao_documentos(
    matricula: Annotated[str, Form()],
    cpf: Annotated[str, Form()],
    email: Annotated[str, Form()],
    tipo_documento: Annotated[str, Form()],
    historico: Annotated[UploadFile, File(description="PDF do histórico acadêmico")],
):
    document_type = DOCUMENT_TYPE_MAP.get(tipo_documento)
    if not document_type:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Tipo de documento inválido.")

    content = await historico.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Arquivo excede 50 MB.")
    if historico.content_type != "application/pdf":
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Apenas arquivos PDF são aceitos.")

    file_obj = _FileLike(content, historico.filename or "historico.pdf")

    form_data = {
        "registration": matricula,
        "cpf": cpf,
        "email": email,
        "document_type": document_type,
    }

    try:
        from backend.infrastructure.documents.emission import process_document_emission_submission
        result = await asyncio.to_thread(
            process_document_emission_submission,
            form_data,
            file_obj,
            notification_recipients=settings.destinatarios or [],
        )
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    except Exception as e:
        logger.error("Erro ao processar Emissão de Documentos:\n%s", traceback.format_exc())
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Erro ao processar documento: {e}")

    if not result.get("success"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, result.get("message", "Validação do histórico falhou."))

    return {
        "status": "emitido",
        "message": result.get("message", "Documento emitido e enviado por e-mail."),
    }
