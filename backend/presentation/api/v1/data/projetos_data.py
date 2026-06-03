from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi import status as http_status
from fastapi import Query
from typing import Optional
from pydantic import BaseModel

from backend.presentation.dependencies import get_admin_dependency

router = APIRouter()

VALID_STATUSES = {"recebido", "iniciado", "cancelado", "terminado"}


class StatusUpdate(BaseModel):
    status: str


@router.get("/projetos", tags=["Consultas"])
async def list_projetos(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(20, ge=1, le=1000),
    natureza: Optional[str] = None,
    status: Optional[str] = None,
    _: str = Depends(get_admin_dependency),
):
    try:
        from backend.infrastructure.database.repository import list_projetos_submissions
        return list_projetos_submissions(
            pagina=pagina,
            por_pagina=por_pagina,
            natureza=natureza,
            status=status,
        )
    except Exception as e:
        raise HTTPException(http_status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))


@router.patch("/projetos/{projeto_id}/status", tags=["Consultas"])
async def update_projeto_status(
    projeto_id: int,
    body: StatusUpdate,
    _: str = Depends(get_admin_dependency),
):
    if body.status not in VALID_STATUSES:
        raise HTTPException(
            http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Status inválido '{body.status}'. Valores aceitos: {sorted(VALID_STATUSES)}",
        )
    try:
        from backend.infrastructure.database.repository import update_projeto_status
        updated = update_projeto_status(projeto_id, body.status)
        if not updated:
            raise HTTPException(http_status.HTTP_404_NOT_FOUND, "Projeto não encontrado")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(http_status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))


@router.delete("/projetos/{projeto_id}", tags=["Consultas"])
async def delete_projeto(
    projeto_id: int,
    _: str = Depends(get_admin_dependency),
):
    try:
        from backend.infrastructure.database.repository import delete_projeto as _delete
        deleted = _delete(projeto_id)
        if not deleted:
            raise HTTPException(http_status.HTTP_404_NOT_FOUND, "Projeto não encontrado")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(http_status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))

