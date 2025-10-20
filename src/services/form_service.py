from __future__ import annotations

from typing import Any, Dict, Iterable

import streamlit as st

from src.models.schemas import AccSubmission
from src.services.email_service import send_notification
from src.services.file_processor import prepare_files, sanitize_submission
from src.services.google_drive import upload_files
from src.services.google_sheets import append_rows


def render_submission_form() -> Dict[str, Any] | None:
    """Renderiza um formulário básico e retorna os dados enviados."""
    with st.form("submission_form"):
        name = st.text_input("Nome completo")
        email = st.text_input("E-mail")
        cpf = st.text_input("CPF")
        uploaded_files = st.file_uploader("Anexar arquivos", accept_multiple_files=True)
        submitted = st.form_submit_button("Enviar")

    if not submitted:
        return None

    return {
        "name": name,
        "email": email,
        "cpf": cpf,
        "files": uploaded_files,
    }


def _coerce_recipients(recipients: Iterable[str] | str | None) -> list[str]:
    if recipients is None:
        return []
    if isinstance(recipients, str):
        return [email.strip() for email in recipients.split(",") if email.strip()]
    return [email.strip() for email in recipients if email.strip()]


def process_acc_submission(
    form_data: Dict[str, Any],
    uploaded_file: Any,
    *,
    drive_folder_id: str = "",
    sheet_id: str = "",
    notification_recipients: Iterable[str] | str | None = None,
) -> AccSubmission:
    """Processa submissões ACC consolidando fluxo Drive/Sheets/E-mail."""
    from datetime import datetime
    
    if uploaded_file is None:
        raise ValueError("Arquivo obrigatório não informado.")

    required_fields = ["name", "registration", "email", "class_group"]
    missing = [field for field in required_fields if not str(form_data.get(field, "")).strip()]
    if missing:
        raise ValueError(f"Campos obrigatórios ausentes: {', '.join(missing)}")

    sanitized = sanitize_submission(form_data)
    prepared_files = list(prepare_files([uploaded_file]))
    if not prepared_files:
        raise ValueError("Nenhum arquivo válido para upload.")

    # Upload com estrutura de pastas: turma/matricula
    uploaded_files_info = upload_files(
        prepared_files, 
        drive_folder_id,
        turma=sanitized["class_group"],
        matricula=sanitized["registration"]
    )
    
    # Extrair IDs e links
    file_ids = [f['id'] for f in uploaded_files_info]
    file_links = [f['webViewLink'] for f in uploaded_files_info]
    file_names = [f['name'] for f in uploaded_files_info]

    # Adicionar dados na planilha
    append_rows(
        [
            {
                "Nome": sanitized["name"],
                "Matrícula": sanitized["registration"],
                "Email": sanitized["email"],
                "Turma": sanitized["class_group"],
                "Arquivos": ", ".join(file_links),  # Usar links ao invés de IDs
            }
        ],
        sheet_id,
    )

    # Enviar email de notificação formatado
    recipients = _coerce_recipients(notification_recipients)
    if recipients:
        # Formatar data/hora atual
        data_formatada = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
        
        # Formatar anexos com links
        anexos_formatados = "\n".join([
            f"    • {name}: {link}"
            for name, link in zip(file_names, file_links)
        ])
        
        subject = "✅ Nova Submissão de ACC Recebida"
        body = f"""\
Olá,

Uma nova resposta foi registrada no formulário de Atividades Curriculares Complementares (ACC).

📅 Data: {data_formatada}
🎓 Nome: {sanitized['name']}
🔢 Matrícula: {sanitized['registration']}
📧 E-mail: {sanitized['email']}
📌 Turma: {sanitized['class_group']}

📎 Anexos: 
{anexos_formatados}

🔗 Você pode acessar os anexos através dos links fornecidos.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Sistema de Automação da FASI
"""
        send_notification(subject, body, recipients)

    return AccSubmission(
        name=sanitized["name"],
        registration=sanitized["registration"],
        email=sanitized["email"],
        class_group=sanitized["class_group"],
        file_ids=file_ids,
    )
