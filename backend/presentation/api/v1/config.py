from fastapi import APIRouter, Query
from backend.config.settings import settings

router = APIRouter()


@router.get("/config/periodos-letivos")
def get_periodos_letivos():
    periodos = [p.strip() for p in settings.periodos_letivos.split(",") if p.strip()]
    return {"periodos": periodos}


@router.get("/config/periodos-submissao")
def get_periodos_submissao(tipo: str = Query(..., description="tcc | acc | estagio")):
    """Retorna todos os períodos de submissão cadastrados para o tipo informado."""
    from backend.infrastructure.database.repository import list_periodos_submissao
    periodos = list_periodos_submissao(tipo=tipo)
    return {"periodos": periodos}
