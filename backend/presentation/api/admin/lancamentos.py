from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
import logging

from backend.presentation.dependencies import get_admin_dependency

router = APIRouter()

logger = logging.getLogger(__name__)


class AtualizarStatusRequest(BaseModel):
    matricula: str
    periodo: str
    polo: str
    componente: str
    matriculado: Optional[bool] = None
    consolidado: Optional[bool] = None


class DeleteLancamentoRequest(BaseModel):
    id: Optional[int] = None
    tipo_formulario: str
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


@router.get("/lancamentos/ccf/{submissao_id}/pdf")
async def baixar_pdf_ccf(submissao_id: int, _: str = Depends(get_admin_dependency)):
    """Retorna o PDF consolidado de uma submissão CCF (armazenado no banco)."""
    from backend.infrastructure.database.repository import get_ccf_pdf

    resultado = get_ccf_pdf(submissao_id)
    if resultado is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "PDF não encontrado")

    content, filename = resultado
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )






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


@router.delete("/lancamentos", status_code=200)
async def delete_lancamento(
    data: DeleteLancamentoRequest,
    _: str = Depends(get_admin_dependency),
):
    """Remove o lançamento, a submissão-fonte e move a pasta do Drive para a lixeira."""
    try:
        from backend.infrastructure.database.repository import (
            delete_lancamento_conceitos_with_source,
            get_lancamento_source_drive_info,
        )

        drive_info = get_lancamento_source_drive_info(
            tipo_formulario=data.tipo_formulario,
            matricula=data.matricula,
            periodo=data.periodo,
            polo=data.polo,
            componente=data.componente,
        )

        deleted, _ = delete_lancamento_conceitos_with_source([{
            "id": data.id,
            "tipo_formulario": data.tipo_formulario,
            "matricula": data.matricula,
            "periodo": data.periodo,
            "polo": data.polo,
            "componente": data.componente,
        }])

        drive_deleted = False
        if drive_info:
            from backend.infrastructure.google.drive import trash_folder_by_path, trash_item
            if drive_info["type"] == "folder":
                drive_deleted = trash_folder_by_path(drive_info["root"], drive_info["path"])
            elif drive_info["type"] == "file":
                drive_deleted = trash_item(drive_info["item_id"])

        logger.info(
            f"[DELETE] {data.tipo_formulario} | {data.matricula} | {data.componente} | "
            f"db_deleted={deleted} | drive_deleted={drive_deleted}"
        )

        return {"ok": True, "deleted": deleted, "drive_deleted": drive_deleted}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[DELETE] Erro: {type(e).__name__}: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))
