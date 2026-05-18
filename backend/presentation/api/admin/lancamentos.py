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
    componente: str  # ACC I, ACC II, ACC III, ACC IV, TCC I, TCC II
    orientador: Optional[str] = None  # Obrigatório para TCC
    conceito: Optional[str] = "E"  # Para consolidação: B, E, I, R, S (padrão: E)


class AtualizarStatusRequest(BaseModel):
    matricula: str
    periodo: str
    polo: str
    componente: str
    matriculado: Optional[bool] = None
    consolidado: Optional[bool] = None


@router.get("/lancamentos/componentes-validos")
async def get_componentes_validos(_: str = Depends(get_admin_dependency)):
    """Retorna lista de componentes válidos para matrícula"""
    from backend.infrastructure.sigaa.lancamento_service import LancamentoService
    return {
        "componentes": sorted(list(LancamentoService.COMPONENTES_VALIDOS)),
        "componentes_expandidos": LancamentoService.COMPONENTES_EXPANDIDOS,
        "descricao": "Componentes válidos para matrícula no SIGAA. ACC e TCC são expandidos automaticamente.",
        "conceitos_validos": ["B", "E", "I", "R", "S"],
        "notas": [
            "ACC → matricula/consolida em ACC I, ACC II, ACC III, ACC IV",
            "TCC → matricula/consolida em TCC I, TCC II",
            "Componentes específicos (ACC I, TCC I, etc.) são processados diretamente",
            "Para TCC, sempre inclua o campo 'orientador'"
        ]
    }


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
    except ValueError as e:
        logger.error(f"[MATRICULAR] Erro de validação: {str(e)}")
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"{str(e)} Consulte GET /api/admin/lancamentos/componentes-validos para a lista correta."
        )
    except Exception as e:
        logger.exception(f"[MATRICULAR] Erro não tratado: {type(e).__name__}: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Erro SIGAA: {e}")


@router.post("/lancamentos/consolidar", status_code=202)
async def consolidar_sigaa(data: LancamentoRequest, _: str = Depends(get_admin_dependency)):
    """Dispara automação Playwright para consolidar conceito no SIGAA."""
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"[CONSOLIDAR] Iniciando consolidação - Matricula: {data.matricula}, Componente: {data.componente}")

        from backend.infrastructure.sigaa.lancamento_service import LancamentoService
        logger.info(f"[CONSOLIDAR] LancamentoService importado com sucesso")

        servico = LancamentoService(
            matricula=data.matricula,
            polo=data.polo,
            periodo=data.periodo,
            componente=data.componente,
            orientador=data.orientador,
        )
        logger.info(f"[CONSOLIDAR] Serviço criado com sucesso")

        logger.info(f"[CONSOLIDAR] Chamando servico.consolidar(conceito={data.conceito})...")
        resultado = await servico.consolidar(conceito=data.conceito)
        logger.info(f"[CONSOLIDAR] Resultado recebido - Sucesso: {resultado.sucesso}")

        if resultado.sucesso:
            logger.info(f"[CONSOLIDAR] Consolidação bem-sucedida: {resultado.mensagem}")
            return {"message": resultado.mensagem, "detalhes": resultado.detalhes}
        else:
            logger.error(f"[CONSOLIDAR] Falha na consolidação: {resultado.mensagem}")
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, resultado.mensagem)
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"[CONSOLIDAR] Erro de validação: {str(e)}")
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"{str(e)} Consulte GET /api/admin/lancamentos/componentes-validos para a lista correta."
        )
    except Exception as e:
        logger.exception(f"[CONSOLIDAR] Erro não tratado: {type(e).__name__}: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Erro SIGAA: {e}")


@router.patch("/lancamentos/atualizar-status")
async def atualizar_status_lancamento(
    data: AtualizarStatusRequest,
    _: str = Depends(get_admin_dependency)
):
    """Atualiza manualmente o status de matriculado e/ou consolidado.

    Use quando o secretário faz a operação diretamente no SIGAA (não pelo FasiTech).
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        from backend.infrastructure.database.repository import atualizar_status_lancamento

        resultado = atualizar_status_lancamento(
            matricula=data.matricula,
            periodo=data.periodo,
            polo=data.polo,
            componente=data.componente,
            matriculado=data.matriculado,
            consolidado=data.consolidado,
        )

        if resultado:
            logger.info(
                f"[STATUS] Atualizado - Matricula: {data.matricula}, "
                f"Componente: {data.componente}, "
                f"Matriculado: {data.matriculado}, Consolidado: {data.consolidado}"
            )
            return {
                "message": "Status atualizado com sucesso",
                "matricula": resultado.matricula,
                "componente": resultado.componente,
                "matriculado": resultado.matriculado,
                "consolidado": resultado.consolidado,
            }
        else:
            logger.error(
                f"[STATUS] Registro não encontrado - Matricula: {data.matricula}, "
                f"Componente: {data.componente}"
            )
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                f"Nenhum lançamento encontrado para: {data.matricula} - {data.componente}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[STATUS] Erro ao atualizar: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Erro ao atualizar status: {str(e)}"
        )
