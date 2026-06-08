from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from backend.presentation.dependencies import get_admin_dependency

router = APIRouter()


class PeriodoRequest(BaseModel):
    tipo: str          # 'tcc' | 'acc' | 'estagio'
    numero: int        # 1-4
    data_inicio: str   # YYYY-MM-DD
    data_fim: str      # YYYY-MM-DD
    semestre: Optional[str] = None


class PeriodoUpdateRequest(BaseModel):
    tipo: Optional[str] = None
    numero: Optional[int] = None
    data_inicio: Optional[str] = None
    data_fim: Optional[str] = None
    semestre: Optional[str] = None


@router.get("/periodos-submissao")
async def list_periodos(_: str = Depends(get_admin_dependency)):
    try:
        from backend.infrastructure.database.repository import list_periodos_submissao
        return list_periodos_submissao()
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))


@router.post("/periodos-submissao", status_code=201)
async def create_periodo(data: PeriodoRequest, _: str = Depends(get_admin_dependency)):
    try:
        from backend.infrastructure.database.repository import save_periodo_submissao
        periodo_id = save_periodo_submissao(data.model_dump())
        return {"id": periodo_id, "message": "Período criado com sucesso"}
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))


@router.put("/periodos-submissao/{periodo_id}")
async def update_periodo(periodo_id: int, data: PeriodoUpdateRequest, _: str = Depends(get_admin_dependency)):
    try:
        from backend.infrastructure.database.repository import update_periodo_submissao
        updated = update_periodo_submissao(periodo_id, {k: v for k, v in data.model_dump().items() if v is not None})
        if not updated:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Período não encontrado")
        return {"message": "Período atualizado com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))


@router.delete("/periodos-submissao/{periodo_id}", status_code=204)
async def delete_periodo(periodo_id: int, _: str = Depends(get_admin_dependency)):
    try:
        from backend.infrastructure.database.repository import delete_periodo_submissao
        deleted = delete_periodo_submissao(periodo_id)
        if not deleted:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Período não encontrado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))
