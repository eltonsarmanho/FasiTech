from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import Optional

from backend.presentation.dependencies import get_admin_dependency
from backend.presentation.schemas.forms import RequerimentoTccFormRequest, SubmissionResult

router = APIRouter()


def _validate_requerimento_tcc_payload(
    data: RequerimentoTccFormRequest,
    *,
    exclude_submission_id: int | None = None,
) -> None:
    if data.horario_defesa:
        from backend.infrastructure.database.repository import _parse_horario_minutos

        if _parse_horario_minutos(data.horario_defesa) is None:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"Horário '{data.horario_defesa}' inválido. Use o formato HH:MM (ex: 14:30).",
            )

    banca_campos = [data.orientador, data.membro_banca1, data.membro_banca2, data.membro_banca3]
    banca_nomes = [b.strip().lower() for b in banca_campos if b]
    if len(banca_nomes) != len(set(banca_nomes)):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Há membros duplicados na composição da banca (mesmo nome em mais de um campo).",
        )

    if data.data_defesa:
        from backend.infrastructure.database.repository import get_periodos_ativos_para_data, list_periodos_submissao

        periodos_validos = get_periodos_ativos_para_data("tcc", data.data_defesa)
        if not periodos_validos:
            todos_periodos = list_periodos_submissao(tipo="tcc")
            if todos_periodos:
                detalhes = "; ".join(
                    f"Período {p['numero']}: {p['data_inicio']} a {p['data_fim']}"
                    for p in todos_periodos
                )
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    f"A data de defesa deve estar dentro de um período de defesa. Períodos disponíveis: {detalhes}",
                )

    if data.data_defesa and data.horario_defesa:
        from backend.infrastructure.database.repository import check_tcc_scheduling_conflicts

        conflicts = check_tcc_scheduling_conflicts(
            data.model_dump(),
            exclude_matricula=None if exclude_submission_id is not None else data.matricula,
            exclude_submission_id=exclude_submission_id,
        )
        if conflicts:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                {"type": "cruzamento_horario", "conflitos": conflicts},
            )


def _enviar_ata_requerimento(submission_id: int) -> dict:
    from backend.infrastructure.database.repository import (
        list_requerimento_tcc_submissions,
        list_funcionarios,
    )
    from backend.infrastructure.documents.ata_defesa import enviar_ata_por_email

    result = list_requerimento_tcc_submissions(pagina=1, por_pagina=500)
    items = result.get("items", [])
    requerimento = next((r for r in items if r.get("id") == submission_id), None)
    if not requerimento:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Requerimento não encontrado")

    funcionarios = list_funcionarios()
    enviar_ata_por_email(requerimento, funcionarios)
    return requerimento


@router.get("/requerimento-tcc", tags=["Consultas"])
async def list_requerimento_tcc(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(20, ge=1, le=500),
    turma: Optional[str] = None,
    _: str = Depends(get_admin_dependency),
):
    try:
        from backend.infrastructure.database.repository import list_requerimento_tcc_submissions
        return list_requerimento_tcc_submissions(pagina=pagina, por_pagina=por_pagina, turma=turma)
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))


@router.post("/requerimento-tcc/gerar-ata-lote", tags=["Consultas"])
async def gerar_ata_defesa_lote(
    payload: dict = Body(...),
    _: str = Depends(get_admin_dependency),
):
    """Gera e envia ATAs em lote para os requerimentos selecionados."""
    submission_ids = payload.get("submission_ids")
    if not isinstance(submission_ids, list) or not submission_ids:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Informe ao menos um registro para disparo em lote.")

    enviados = []
    falhas = []
    for raw_id in submission_ids:
        try:
            submission_id = int(raw_id)
            requerimento = _enviar_ata_requerimento(submission_id)
            enviados.append({
                "id": submission_id,
                "nome_aluno": requerimento.get("nome_aluno"),
                "orientador": requerimento.get("orientador"),
            })
        except HTTPException as exc:
            falhas.append({
                "id": raw_id,
                "detail": exc.detail,
            })
        except Exception as exc:
            falhas.append({
                "id": raw_id,
                "detail": str(exc),
            })

    return {
        "ok": len(enviados) > 0,
        "total": len(submission_ids),
        "enviados": enviados,
        "falhas": falhas,
        "message": f"{len(enviados)} ATA(s) enviada(s) e {len(falhas)} falha(s).",
    }


@router.post("/requerimento-tcc/{submission_id}/gerar-ata", tags=["Consultas"])
async def gerar_ata_defesa(
    submission_id: int,
    _: str = Depends(get_admin_dependency),
):
    """Gera a ATA de Defesa em .docx e envia por e-mail ao orientador."""
    try:
        requerimento = _enviar_ata_requerimento(submission_id)
        return {"ok": True, "message": f"ATA enviada para o e-mail do orientador ({requerimento.get('orientador')})"}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))


@router.get("/requerimento-tcc/{submission_id}", tags=["Consultas"])
async def get_requerimento_tcc(
    submission_id: int,
    _: str = Depends(get_admin_dependency),
):
    try:
        from backend.infrastructure.database.repository import get_requerimento_tcc_submission

        row = get_requerimento_tcc_submission(submission_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Registro não encontrado")
        return row
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))


@router.put("/requerimento-tcc/{submission_id}", response_model=SubmissionResult, tags=["Consultas"])
async def update_requerimento_tcc(
    submission_id: int,
    data: RequerimentoTccFormRequest,
    _: str = Depends(get_admin_dependency),
):
    try:
        _validate_requerimento_tcc_payload(data, exclude_submission_id=submission_id)

        from backend.infrastructure.database.repository import update_requerimento_tcc_submission

        updated_id = update_requerimento_tcc_submission(submission_id, data.model_dump())
        if updated_id is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Registro não encontrado")
        return SubmissionResult(
            id=updated_id,
            status="recebido",
            message="Requerimento de TCC atualizado com sucesso!",
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))


@router.delete("/requerimento-tcc/{submission_id}", tags=["Consultas"], status_code=200)
async def delete_requerimento_tcc(
    submission_id: int,
    _: str = Depends(get_admin_dependency),
):
    try:
        from backend.infrastructure.database.repository import (
            delete_requerimento_tcc_submission,
            get_requerimento_tcc_drive_info,
        )

        drive_info = get_requerimento_tcc_drive_info(submission_id)

        deleted = delete_requerimento_tcc_submission(submission_id)
        if not deleted:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Registro não encontrado")

        drive_deleted = False
        if drive_info and drive_info.get("type") == "folder":
            try:
                from backend.infrastructure.google.drive import trash_folder_by_path
                drive_deleted = trash_folder_by_path(drive_info["root"], drive_info["path"])
            except Exception as drive_error:
                print(f"⚠️ Erro ao deletar pasta no Drive: {str(drive_error)}")

        return {"ok": True, "drive_deleted": drive_deleted}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))
