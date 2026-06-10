from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

from backend.presentation.dependencies import get_admin_dependency

router = APIRouter()


@router.get("/requerimento-tcc", tags=["Consultas"])
async def list_requerimento_tcc(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(20, ge=1, le=500),
    turma: Optional[str] = None,
    _: str = Depends(get_admin_dependency),
):
    try:
        from backend.infrastructure.database.repository import list_requerimento_tcc_submissions
        return list_requerimento_tcc_submissions(pagina=pagina, por_pagina=por_pagina, turma=turma)
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))


@router.delete("/requerimento-tcc/{submission_id}", tags=["Consultas"], status_code=200)
async def delete_requerimento_tcc(
    submission_id: int,
    _: str = Depends(get_admin_dependency),
):
    try:
        from backend.infrastructure.database.repository import delete_requerimento_tcc_submission
        deleted = delete_requerimento_tcc_submission(submission_id)
        if not deleted:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Registro não encontrado")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))


@router.post("/requerimento-tcc/{submission_id}/gerar-ata", tags=["Consultas"])
async def gerar_ata_defesa(
    submission_id: int,
    _: str = Depends(get_admin_dependency),
):
    """Gera a ATA de Defesa em .docx e envia por e-mail ao orientador."""
    try:
        from backend.infrastructure.database.repository import (
            list_requerimento_tcc_submissions,
            list_funcionarios,
        )
        from backend.infrastructure.documents.ata_defesa import enviar_ata_por_email

        # Busca o requerimento pelo ID
        result = list_requerimento_tcc_submissions(pagina=1, por_pagina=500)
        items = result.get("items", [])
        requerimento = next((r for r in items if r.get("id") == submission_id), None)
        if not requerimento:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Requerimento não encontrado")

        funcionarios = list_funcionarios()
        enviar_ata_por_email(requerimento, funcionarios)
        return {"ok": True, "message": f"ATA enviada para o e-mail do orientador ({requerimento.get('orientador')})"}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))
