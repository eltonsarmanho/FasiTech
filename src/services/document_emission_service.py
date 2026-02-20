from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
import re

from src.services.StatusAlunoExtractor import StatusAlunoExtractor
from src.services.email_service import send_email_with_attachments
from src.services.file_processor import sanitize_submission
from src.services.gerador_certificado import assinar_pdf
from src.utils.PDFGenerator import (
    gerar_pdf_comprovante_conclusao,
    gerar_pdf_comprovante_matricula_ativa,
)

DOCUMENTO_CONCLUSAO = "Comprovante de Conclusão de Curso"
DOCUMENTO_MATRICULA = "Comprovante de Matrícula Ativa"
TIPOS_DOCUMENTO_VALIDOS = {DOCUMENTO_CONCLUSAO, DOCUMENTO_MATRICULA}


def _coerce_recipients(recipients: Iterable[str] | str | None) -> list[str]:
    if recipients is None:
        return []
    if isinstance(recipients, str):
        return [email.strip() for email in recipients.split(",") if email.strip()]
    return [email.strip() for email in recipients if email.strip()]


def _semestre_atual() -> str:
    hoje = datetime.now()
    semestre = 1 if hoje.month <= 6 else 2
    return f"{hoje.year}.{semestre}"


def _validar_dados(form_data: dict[str, Any], uploaded_file: Any) -> None:
    required_fields = ["registration", "cpf", "email", "document_type"]
    missing = [field for field in required_fields if not str(form_data.get(field, "")).strip()]
    if missing:
        raise ValueError(f"Campos obrigatórios ausentes: {', '.join(missing)}")

    if uploaded_file is None:
        raise ValueError("Anexo do histórico acadêmico é obrigatório.")

    if getattr(uploaded_file, "type", "") != "application/pdf":
        raise ValueError("Apenas arquivos PDF são aceitos.")

    document_type = str(form_data.get("document_type", "")).strip()
    if document_type not in TIPOS_DOCUMENTO_VALIDOS:
        raise ValueError("Tipo de documento inválido.")

    matricula = re.sub(r"\D", "", str(form_data.get("registration", "")))
    if len(matricula) != 12:
        raise ValueError("Matrícula deve conter 12 dígitos.")

    cpf_digits = re.sub(r"\D", "", str(form_data.get("cpf", "")))
    if len(cpf_digits) != 11:
        raise ValueError("CPF deve conter 11 dígitos.")


def _formatar_cpf(cpf: str) -> str:
    cpf_digits = re.sub(r"\D", "", cpf or "")
    if len(cpf_digits) != 11:
        return ""
    return f"{cpf_digits[:3]}.{cpf_digits[3:6]}.{cpf_digits[6:9]}-{cpf_digits[9:]}"


def process_document_emission_submission(
    form_data: dict[str, Any],
    uploaded_file: Any,
    *,
    notification_recipients: Iterable[str] | str | None = None,
) -> dict[str, Any]:
    """
    Processa a emissão de comprovantes com validação do histórico acadêmico.
    """
    _validar_dados(form_data, uploaded_file)
    sanitized = sanitize_submission(form_data)

    uploaded_file.seek(0)
    pdf_bytes = uploaded_file.read()
    if not pdf_bytes:
        raise ValueError("Não foi possível ler o PDF enviado.")

    matricula = str(sanitized.get("registration", "")).strip()
    cpf_informado = _formatar_cpf(str(form_data.get("cpf", "")).strip())
    email = str(sanitized.get("email", "")).strip()
    document_type = str(form_data.get("document_type", "")).strip()
    semestre = _semestre_atual()

    try:
        StatusAlunoExtractor.validar_documento_historico(pdf_bytes)

        if document_type == DOCUMENTO_CONCLUSAO:
            status_aprovado = StatusAlunoExtractor.aluno_integralizou(pdf_bytes)
            if not status_aprovado:
                return {
                    "success": False,
                    "message": "Histórico indica que a integralização ainda não foi concluída.",
                }
        else:
            status_aprovado = StatusAlunoExtractor.aluno_matriculado(pdf_bytes)
            if not status_aprovado:
                return {
                    "success": False,
                    "message": f"Histórico não apresenta matrícula ativa no semestre {semestre}.",
                }
    except ValueError as exc:
        return {
            "success": False,
            "message": f"Não foi possível validar o histórico acadêmico: {exc}",
        }
    except Exception as exc:
        return {
            "success": False,
            "message": f"Falha ao analisar o histórico acadêmico: {exc}",
        }

    dados_aluno = StatusAlunoExtractor.extrair_dados_aluno(pdf_bytes)
    nome = dados_aluno.get("nome", "")
    cpf_extraido = dados_aluno.get("cpf", "")
    cpf_final = cpf_informado or cpf_extraido
    ultimo_periodo = StatusAlunoExtractor.extrair_ultimo_periodo_componente(pdf_bytes)
    periodo_matriculado = StatusAlunoExtractor.extrair_periodo_matriculado(pdf_bytes)

    if document_type == DOCUMENTO_CONCLUSAO:
        periodo_referencia = ultimo_periodo if ultimo_periodo else semestre
        caminho_pdf, layout_info = gerar_pdf_comprovante_conclusao(
            nome=nome,
            matricula=matricula,
            cpf=cpf_final,
            periodo_letivo=f"semestre letivo {periodo_referencia}",
            return_layout=True,
        )
    else:
        periodo_referencia = periodo_matriculado if periodo_matriculado else semestre
        caminho_pdf, layout_info = gerar_pdf_comprovante_matricula_ativa(
            nome=nome,
            matricula=matricula,
            cpf=cpf_final,
            semestre_atual=f"semestre letivo {periodo_referencia}",
            return_layout=True,
        )

    caminho_assinado = assinar_pdf(
        caminho_pdf,
        anchor_x=float(layout_info.get("center_x", 0)),
        anchor_y=float(layout_info.get("line_y", 0)),
    )

    recipients = _coerce_recipients(notification_recipients)
    if email and email not in recipients:
        recipients.insert(0, email)

    if recipients:
        subject = f"✅ {document_type} - FASI/UFPA"
        body = (
            "Olá,\n\n"
            f"Seu documento '{document_type}' foi emitido com sucesso.\n\n"
            f"Matrícula: {matricula}\n"
            f"Semestre de referência: {periodo_referencia}\n"
            f"Data de emissão: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
            "O comprovante assinado digitalmente segue em anexo.\n\n"
            "Atenciosamente,\n"
            "Sistema de Automação da FASI"
        )
        send_email_with_attachments(subject, body, recipients, [caminho_assinado])

    caminho_final = Path(caminho_assinado)
    if caminho_final.exists():
        caminho_final.unlink()

    return {
        "success": True,
        "message": f"{document_type} emitido e enviado para {email}.",
    }
