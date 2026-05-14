from fastapi import APIRouter
from backend.config.settings import settings

router = APIRouter()


@router.get("/config/periodos-letivos")
def get_periodos_letivos():
    periodos = [p.strip() for p in settings.periodos_letivos.split(",") if p.strip()]
    return {"periodos": periodos}
