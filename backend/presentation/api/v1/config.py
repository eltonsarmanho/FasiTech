from typing import Optional

from fastapi import APIRouter, Query
from backend.config.settings import settings

router = APIRouter()


@router.get("/config/periodos-letivos")
def get_periodos_letivos():
    periodos = [p.strip() for p in settings.periodos_letivos.split(",") if p.strip()]
    return {"periodos": periodos}


@router.get("/funcionarios")
def get_funcionarios_publico(
    categoria: Optional[str] = Query(None, description="Docente | Secretaria | Colaborador"),
    tipo: Optional[str] = Query(None, description="Interno | Externo"),
):
    """Lista pública (sem e-mail/contato) de funcionários para popular seletores
    nos formulários. Filtra por categoria e/ou tipo."""
    from backend.infrastructure.database.repository import list_funcionarios

    funcionarios = list_funcionarios(tipo=tipo)
    if categoria:
        funcionarios = [f for f in funcionarios if (f.get("categoria") or "") == categoria]
    # Expõe apenas dados não sensíveis necessários para os seletores
    return {
        "funcionarios": [
            {
                "nome": f["nome"],
                "titulo": f.get("titulo"),
                "tipo": f.get("tipo"),
                "categoria": f.get("categoria"),
            }
            for f in funcionarios
        ]
    }


@router.get("/config/periodos-submissao")
def get_periodos_submissao(tipo: str = Query(..., description="tcc | acc | estagio")):
    """Retorna todos os períodos de submissão cadastrados para o tipo informado."""
    from backend.infrastructure.database.repository import list_periodos_submissao
    periodos = list_periodos_submissao(tipo=tipo)
    return {"periodos": periodos}
