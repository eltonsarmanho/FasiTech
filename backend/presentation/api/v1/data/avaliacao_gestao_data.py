from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional

from backend.presentation.dependencies import get_admin_dependency

router = APIRouter()


@router.get("/avaliacao-gestao", tags=["Consultas"])
async def list_avaliacao_gestao(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(500, ge=1, le=2000),
    periodo: Optional[str] = None,
    _: str = Depends(get_admin_dependency),
):
    try:
        from backend.infrastructure.database.repository import list_avaliacao_gestao_submissions
        return list_avaliacao_gestao_submissions(
            pagina=pagina,
            por_pagina=por_pagina,
            periodo=periodo,
        )
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))
