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
    logger.info(
        "emissao-documentos: matricula=%s tipo=%s filename=%s content_type=%s",
        matricula, tipo_documento,
        getattr(historico, "filename", "?"),
        getattr(historico, "content_type", "?"),
    )

    document_type = DOCUMENT_TYPE_MAP.get(tipo_documento)
    if not document_type:
        logger.warning("emissao-documentos: tipo_documento inválido=%r", tipo_documento)
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Tipo de documento inválido.")

    content = await historico.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Arquivo excede 50 MB.")
    if historico.content_type != "application/pdf":
        logger.warning(
            "emissao-documentos: content_type inesperado=%r (matricula=%s)",
            historico.content_type, matricula,
        )
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Apenas arquivos PDF são aceitos.")

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
        logger.warning("emissao-documentos: ValueError matricula=%s | %s", matricula, e)
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e))
    except Exception as e:
        logger.error("Erro ao processar Emissão de Documentos:\n%s", traceback.format_exc())
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Erro ao processar documento: {e}")

    if not result.get("success"):
        logger.warning(
            "emissao-documentos: rejeitado matricula=%s | %s",
            matricula, result.get("message"),
        )
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, result.get("message", "Validação do histórico falhou."))

    return {
        "status": "emitido",
        "message": result.get("message", "Documento emitido e enviado por e-mail."),
    }
