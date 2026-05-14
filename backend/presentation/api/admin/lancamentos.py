from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional

from backend.presentation.dependencies import get_admin_dependency

router = APIRouter()


class LancamentoRequest(BaseModel):
    matricula: str
    periodo: str
    polo: str
    componente: str


@router.get("/lancamentos")
async def list_lancamentos(
    tipo_formulario: str = Query(..., description="ACC, TCC ou Estagio"),
    polo: Optional[str] = None,
    periodo: Optional[str] = None,
    turma: Optional[str] = None,
    componente_estagio: Optional[str] = None,
    _: str = Depends(get_admin_dependency),
):
    try:
        from backend.infrastructure.database.repository import get_lancamento_conceitos
        return get_lancamento_conceitos(
            tipo_formulario=tipo_formulario,
            polo=polo,
            periodo=periodo,
            turma=turma,
            componente_estagio=componente_estagio,
        )
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))


@router.post("/lancamentos/matricular", status_code=202)
async def matricular_sigaa(data: LancamentoRequest, _: str = Depends(get_admin_dependency)):
    """Dispara automação Playwright para matricular aluno no SIGAA."""
    try:
        from backend.infrastructure.sigaa.matricular import matricular_aluno
        await matricular_aluno(
            matricula=data.matricula, periodo=data.periodo,
            polo=data.polo, componente=data.componente,
        )
        return {"message": f"Matrícula do aluno {data.matricula} iniciada no SIGAA"}
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Erro SIGAA: {e}")


@router.post("/lancamentos/consolidar", status_code=202)
async def consolidar_sigaa(data: LancamentoRequest, _: str = Depends(get_admin_dependency)):
    """Dispara automação Playwright para consolidar conceito no SIGAA."""
    try:
        from backend.infrastructure.sigaa.consolidar import consolidar_aluno
        await consolidar_aluno(
            matricula=data.matricula, periodo=data.periodo,
            polo=data.polo, componente=data.componente,
        )
        return {"message": f"Consolidação do aluno {data.matricula} iniciada no SIGAA"}
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Erro SIGAA: {e}")
