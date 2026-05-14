from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.presentation.dependencies import get_admin_dependency
from backend.presentation.schemas.forms import AlertaRequest

router = APIRouter()


@router.get("/alertas")
async def list_alertas(_: str = Depends(get_admin_dependency)):
    try:
        from backend.infrastructure.database.repository import get_all_alertas
        return get_all_alertas()
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))


@router.post("/alertas", status_code=201)
async def create_alerta(data: AlertaRequest, _: str = Depends(get_admin_dependency)):
    try:
        from backend.infrastructure.database.repository import create_alerta as _create
        alerta_id = _create(data.model_dump())
        return {"id": alerta_id, "message": "Alerta criado com sucesso"}
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))


@router.put("/alertas/{alerta_id}")
async def update_alerta(alerta_id: int, data: AlertaRequest, _: str = Depends(get_admin_dependency)):
    try:
        from backend.infrastructure.database.repository import update_alerta as _update
        _update(alerta_id, data.model_dump())
        return {"id": alerta_id, "message": "Alerta atualizado"}
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))


@router.delete("/alertas/{alerta_id}", status_code=204)
async def delete_alerta(alerta_id: int, _: str = Depends(get_admin_dependency)):
    try:
        from backend.infrastructure.database.repository import delete_alerta as _delete
        _delete(alerta_id)
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))


@router.post("/alertas/{alerta_id}/disparar")
async def disparar_alerta(alerta_id: int, _: str = Depends(get_admin_dependency)):
    try:
        from backend.infrastructure.scheduler.alert_scheduler import fire_alert
        ok, msg = fire_alert(alerta_id)
        if not ok:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, msg)
        return {"message": msg}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))
