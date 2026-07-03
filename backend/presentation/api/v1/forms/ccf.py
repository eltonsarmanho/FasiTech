from __future__ import annotations

import io
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from typing import Annotated

from backend.presentation.schemas.forms import SubmissionResult

router = APIRouter()

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


class _FileLike(io.BytesIO):
    """BytesIO wrapper que carrega um atributo filename para compatibilidade legada."""
    def __init__(self, data: bytes, name: str):
        super().__init__(data)
        self.name = name


@router.post("/ccf", response_model=SubmissionResult, status_code=201)
async def submit_ccf(
    nome: Annotated[str, Form()],
    matricula: Annotated[str, Form()],
    email: Annotated[str, Form()],
    turma: Annotated[str, Form()],
    polo: Annotated[str, Form()],
    periodo: Annotated[str, Form()],
    arquivo_pdf: Annotated[UploadFile, File(description="PDF consolidado das atividades CCF (máx 50MB)")],
    disciplinas: Annotated[
        list[str],
        Form(description="Nomes das disciplinas flexibilizadas (opcional, porém recomendado). Envie um campo 'disciplinas' por disciplina — quantidade livre."),
    ] = [],
):
    # Valida que o envio ocorre dentro de um período de submissão de CCF
    from datetime import date as _date
    from backend.infrastructure.database.repository import (
        get_periodos_ativos_para_data,
        list_periodos_submissao,
        ccf_already_submitted,
    )
    hoje = _date.today().isoformat()

    if ccf_already_submitted(matricula, polo, periodo):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Você já enviou seu CCF para este período letivo. Não é permitido um segundo envio.",
        )

    if not get_periodos_ativos_para_data("ccf", hoje):
        todos_periodos = list_periodos_submissao(tipo="ccf")
        if todos_periodos:
            detalhes = "; ".join(
                f"Período {p['numero']}: {p['data_inicio']} a {p['data_fim']}"
                for p in todos_periodos
            )
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"O envio de CCF só é permitido durante os períodos de submissão. Períodos: {detalhes}",
            )

    content = await arquivo_pdf.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Arquivo excede 50MB")

    form_data = {
        "name": nome,
        "registration": matricula,
        "email": email,
        "class_group": turma,
        "polo": polo,
        "periodo": periodo,
        "disciplinas": disciplinas,
    }
    uploaded_file = _FileLike(content, arquivo_pdf.filename or "ccf.pdf")

    try:
        from backend.infrastructure.form_service_legacy import process_ccf_submission
        # Destinatários (base de dados): Diretor + Secretário(a). O aluno é
        # incluído internamente pelo serviço.
        from backend.infrastructure.database.repository import (
            get_funcionario_emails_by_cargo,
            get_funcionario_emails,
        )
        recipients: list[str] = []
        for recipient_email in [
            *get_funcionario_emails_by_cargo("diretor_faculdade"),
            *get_funcionario_emails(categoria="Secretaria"),
        ]:
            if recipient_email and recipient_email not in recipients:
                recipients.append(recipient_email)
        result = process_ccf_submission(
            form_data,
            uploaded_file,
            notification_recipients=recipients,
        )
        return SubmissionResult(
            id=result.get("id", 0),
            status="recebido",
            message="CCF enviado com sucesso! Você receberá confirmação por e-mail.",
            drive_links=[],
        )
    except ValueError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Erro ao processar CCF: {e}")
