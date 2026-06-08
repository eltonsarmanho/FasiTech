from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from backend.presentation.schemas.forms import RequerimentoTccFormRequest, SubmissionResult

router = APIRouter()


@router.post("/requerimento-tcc", response_model=SubmissionResult, status_code=201)
async def submit_requerimento_tcc(data: RequerimentoTccFormRequest):
    # Valida que a data de defesa está dentro de um período cadastrado
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

    try:
        from backend.infrastructure.form_service_legacy import process_requerimento_tcc_submission
        result = process_requerimento_tcc_submission(**data.model_dump())
        return SubmissionResult(
            id=result.get("id", 0),
            status="recebido",
            message="Requerimento de TCC registrado com sucesso!",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Erro ao registrar requerimento: {e}")
