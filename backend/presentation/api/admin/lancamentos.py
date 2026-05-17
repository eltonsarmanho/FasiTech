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
    orientador: Optional[str] = None  # Obrigatório para TCC
    conceito: Optional[str] = "E"  # Para consolidação: A, B, C, D, E (padrão: E)


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
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"[MATRICULAR] Iniciando matrícula - Matricula: {data.matricula}, Polo: {data.polo}, Componente: {data.componente}")

        from backend.infrastructure.sigaa.lancamento_service import LancamentoService
        logger.info(f"[MATRICULAR] LancamentoService importado com sucesso")

        servico = LancamentoService(
            matricula=data.matricula,
            polo=data.polo,
            periodo=data.periodo,
            componente=data.componente,
            orientador=data.orientador,
        )
        logger.info(f"[MATRICULAR] Serviço criado com sucesso")

        logger.info(f"[MATRICULAR] Chamando servico.matricular()...")
        resultado = await servico.matricular()
        logger.info(f"[MATRICULAR] Resultado recebido - Sucesso: {resultado.sucesso}")

        if resultado.sucesso:
            logger.info(f"[MATRICULAR] Matrícula bem-sucedida: {resultado.mensagem}")
            return {"message": resultado.mensagem, "detalhes": resultado.detalhes}
        else:
            logger.error(f"[MATRICULAR] Falha na matrícula: {resultado.mensagem}")
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, resultado.mensagem)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[MATRICULAR] Erro não tratado: {type(e).__name__}: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Erro SIGAA: {e}")


@router.post("/lancamentos/consolidar", status_code=202)
async def consolidar_sigaa(data: LancamentoRequest, _: str = Depends(get_admin_dependency)):
    """Dispara automação Playwright para consolidar conceito no SIGAA."""
    try:
        from backend.infrastructure.sigaa.lancamento_service import LancamentoService
        servico = LancamentoService(
            matricula=data.matricula,
            polo=data.polo,
            periodo=data.periodo,
            componente=data.componente,
            orientador=data.orientador,
        )
        resultado = await servico.consolidar(conceito=data.conceito)
        if resultado.sucesso:
            return {"message": resultado.mensagem, "detalhes": resultado.detalhes}
        else:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, resultado.mensagem)
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Erro SIGAA: {e}")
