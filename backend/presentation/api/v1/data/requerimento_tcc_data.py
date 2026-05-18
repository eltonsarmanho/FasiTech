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
