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
