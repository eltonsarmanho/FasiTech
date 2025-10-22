from __future__ import annotations

from typing import Any, Dict, Iterable
import os
import tempfile

import streamlit as st

from src.models.schemas import AccSubmission
from src.services.email_service import send_notification, send_email_with_attachments
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
    processar_com_ia: bool = False,
) -> AccSubmission:
    """Processa submissões ACC consolidando fluxo Drive/Sheets/E-mail e opcionalmente IA."""
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

    # Processar PDF com IA se solicitado
    txt_path = None
    total_carga_horaria = None
    
    if processar_com_ia:
        try:
            print("\n🤖 Processando certificados ACC com IA...")
            
            # Salvar PDF temporariamente para processamento
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                uploaded_file.seek(0)
                tmp_file.write(uploaded_file.read())
                tmp_pdf_path = tmp_file.name
            
            # Importar e processar com AccProcessor
            from src.services.acc_processor import processar_certificados_acc
            
            resultado = processar_certificados_acc(
                pdf_path=tmp_pdf_path,
                matricula=sanitized["registration"],
                nome=sanitized["name"]
            )
            
            txt_path = resultado.get("txt_path")
            total_carga_horaria = resultado.get("total_geral")
            
            # Limpar arquivo temporário
            os.remove(tmp_pdf_path)
            
            print(f"✅ Processamento IA concluído: {total_carga_horaria}")
            
        except Exception as e:
            print(f"⚠️ Erro no processamento com IA: {str(e)}")
            print("   Continuando sem análise de IA...")

    # Adicionar dados na planilha
    row_data = {
        "Nome": sanitized["name"],
        "Matrícula": sanitized["registration"],
        "Email": sanitized["email"],
        "Turma": sanitized["class_group"],
        "Arquivos": ", ".join(file_links),
    }
    
    if total_carga_horaria:
        row_data["Carga Horária"] = total_carga_horaria
    
    append_rows([row_data], sheet_id)

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
        
        # Adicionar informação de carga horária se disponível
        info_carga = ""
        if total_carga_horaria:
            info_carga = f"\n⏱️  {total_carga_horaria}\n"
        
        subject = "✅ Nova Submissão de ACC Recebida"
        body = f"""\
Olá,

Uma nova resposta foi registrada no formulário de Atividades Curriculares Complementares (ACC).

📅 Data: {data_formatada}
🎓 Nome: {sanitized['name']}
🔢 Matrícula: {sanitized['registration']}
📧 E-mail: {sanitized['email']}
📌 Turma: {sanitized['class_group']}{info_carga}

📎 Anexos: 
{anexos_formatados}

🔗 Você pode acessar os anexos através dos links fornecidos.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Sistema de Automação da FASI
"""
        
        # Enviar com anexo TXT se disponível
        attachments = [txt_path] if txt_path else None
        send_email_with_attachments(subject, body, recipients, attachments)

    return AccSubmission(
        name=sanitized["name"],
        registration=sanitized["registration"],
        email=sanitized["email"],
        class_group=sanitized["class_group"],
        file_ids=file_ids,
    )


def process_tcc_submission(
    form_data: Dict[str, Any],
    uploaded_files: list[Any],
    *,
    drive_folder_id: str = "",
    sheet_id: str = "",
    notification_recipients: Iterable[str] | str | None = None,
) -> Dict[str, Any]:
    """Processa submissões TCC consolidando fluxo Drive/Sheets/E-mail.
    
    Args:
        form_data: Dados do formulário contendo:
            - name: Nome completo
            - registration: Matrícula
            - email: E-mail
            - class_group: Turma (ano de ingresso)
            - orientador: Nome do orientador
            - titulo: Título do TCC
            - componente: "TCC 1" ou "TCC 2"
        uploaded_files: Lista de arquivos PDF para upload
        drive_folder_id: ID da pasta do Google Drive
        sheet_id: ID da planilha do Google Sheets
        notification_recipients: Lista de e-mails para notificação
        
    Returns:
        Dicionário com informações do processamento
    """
    from datetime import datetime
    
    if not uploaded_files or len(uploaded_files) == 0:
        raise ValueError("Pelo menos um arquivo é obrigatório.")

    required_fields = ["name", "registration", "email", "class_group", "orientador", "titulo", "componente"]
    missing = [field for field in required_fields if not str(form_data.get(field, "")).strip()]
    if missing:
        raise ValueError(f"Campos obrigatórios ausentes: {', '.join(missing)}")

    # Validar quantidade de arquivos para TCC 2
    componente = form_data.get("componente", "").strip()
    if componente == "TCC 2" and len(uploaded_files) < 3:
        raise ValueError(
            "TCC 2 requer no mínimo 3 arquivos: "
            "Declaração de Autoria, Termo de Autorização e TCC Final."
        )

    sanitized = sanitize_submission(form_data)
    prepared_files = list(prepare_files(uploaded_files))
    
    if not prepared_files:
        raise ValueError("Nenhum arquivo válido para upload.")

    # Upload com estrutura hierárquica: TCC 1 ou TCC 2 / Turma / Nome do Aluno
    # Importar função auxiliar para criar pastas hierárquicas
    from src.services.google_drive import upload_files_tcc
    
    uploaded_files_info = upload_files_tcc(
        prepared_files, 
        drive_folder_id,
        componente=componente,  # "TCC 1" ou "TCC 2"
        turma=sanitized['class_group'],  # "2027"
        nome_aluno=sanitized['name']  # "João Silva"
    )
    
    # Extrair informações dos arquivos
    file_ids = [f['id'] for f in uploaded_files_info]
    file_links = [f['webViewLink'] for f in uploaded_files_info]
    file_names = [f['name'] for f in uploaded_files_info]

    # Adicionar dados na planilha
    row_data = {
        "Nome": sanitized["name"],
        "Matrícula": sanitized["registration"],
        "Email": sanitized["email"],
        "Turma": sanitized["class_group"],
        "Componente": componente,
        "Orientador": sanitized.get("orientador", form_data.get("orientador", "")),
        "Título": sanitized.get("titulo", form_data.get("titulo", "")),
        "Arquivos": ", ".join(file_links),
        "Quantidade de Anexos": len(file_names),
    }
    
    # Usar mesma aba que ACC: "Respostas ao formulário 1"
    append_rows([row_data], sheet_id, range_name="Respostas ao formulário 1")

    # Enviar email de notificação formatado
    recipients = _coerce_recipients(notification_recipients)
    if recipients:
        # Formatar data/hora atual
        data_formatada = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
        
        # Formatar anexos com links
        anexos_formatados = "\n".join([
            f"    {idx}. {name}\n       🔗 {link}"
            for idx, (name, link) in enumerate(zip(file_names, file_links), 1)
        ])
        
        # Emoji para componente
        componente_emoji = "📘" if componente == "TCC 1" else "📗"
        
        # Adicionar biblioteca para TCC 2
        if componente == "TCC 2":
            recipients.append("bibcameta@ufpa.br")
        
        # Adicionar email do aluno
        aluno_email = sanitized["email"]
        if aluno_email and aluno_email not in recipients:
            recipients.append(aluno_email)
        
        subject = f"✅ Nova Submissão de {componente} Recebida"
        body = f"""\
Olá,

Uma nova resposta foi registrada no formulário de Trabalho de Conclusão de Curso ({componente}).

📅 Data: {data_formatada}
{componente_emoji} Componente: {componente}
🎓 Nome: {sanitized['name']}
🔢 Matrícula: {sanitized['registration']}
📧 E-mail: {sanitized['email']}
📌 Turma: {sanitized['class_group']}
👨‍🏫 Orientador(a): {form_data.get('orientador', '')}
📄 Título: {form_data.get('titulo', '')}

📎 Anexos ({len(file_names)} arquivo(s)): 
{anexos_formatados}

🔗 Você pode acessar os anexos através dos links fornecidos.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Sistema de Automação da FASI
"""
        
        send_email_with_attachments(subject, body, recipients)

    return {
        "name": sanitized["name"],
        "registration": sanitized["registration"],
        "email": sanitized["email"],
        "class_group": sanitized["class_group"],
        "componente": componente,
        "orientador": form_data.get("orientador", ""),
        "titulo": form_data.get("titulo", ""),
        "file_ids": file_ids,
        "file_links": file_links,
        "total_files": len(file_names),
    }


def process_estagio_submission(
    form_data: Dict[str, Any],
    uploaded_files: list[Any],
) -> Dict[str, Any]:
    """Processa submissões de Estágio consolidando fluxo Drive/Sheets/E-mail.
    
    Args:
        form_data: Dados do formulário contendo:
            - nome: Nome completo
            - email: E-mail
            - turma: Turma (ano de ingresso)
            - matricula: Matrícula
            - orientador: Nome do orientador ou supervisor
            - titulo: Título do documento
            - componente: "Plano de Estágio (Estágio I)" ou "Relatório Final (Estágio II)"
        uploaded_files: Lista de arquivos PDF para upload
        
    Returns:
        Dicionário com informações do processamento
    """
    from datetime import datetime
    import streamlit as st
    
    if not uploaded_files or len(uploaded_files) == 0:
        raise ValueError("Pelo menos um arquivo é obrigatório.")

    required_fields = ["nome", "email", "turma", "matricula", "orientador", "titulo", "componente"]
    missing = [field for field in required_fields if not str(form_data.get(field, "")).strip()]
    if missing:
        raise ValueError(f"Campos obrigatórios ausentes: {', '.join(missing)}")

    # Carregar configurações de estágio
    try:
        drive_folder_id = st.secrets["estagio"]["drive_folder_id"]
        sheet_id = st.secrets["estagio"]["sheet_id"]
        notification_recipients = st.secrets["estagio"].get("notification_recipients", [])
    except (KeyError, FileNotFoundError) as e:
        raise ValueError("Configurações de Estágio não encontradas em secrets.toml") from e

    prepared_files = list(prepare_files(uploaded_files))
    
    if not prepared_files:
        raise ValueError("Nenhum arquivo válido para upload.")

    # Upload com estrutura hierárquica: Componente Curricular / Turma / Arquivos
    # Extrair componente simplificado (Plano de Estágio ou Relatório Final)
    componente_simplificado = form_data["componente"].split(" (")[0]  # "Plano de Estágio" ou "Relatório Final"
    
    uploaded_files_info = upload_files(
        prepared_files, 
        drive_folder_id,
        turma=form_data['turma'],
        componente=componente_simplificado
    )
    
    # Extrair informações dos arquivos
    file_ids = [f['id'] for f in uploaded_files_info]
    file_links = [f['webViewLink'] for f in uploaded_files_info]
    file_names = [f['name'] for f in uploaded_files_info]

    # Adicionar dados na planilha
    row_data = {
        "Nome do Aluno": form_data["nome"],
        "Email": form_data["email"],
        "Turma": form_data["turma"],
        "Matrícula": form_data["matricula"],
        "Orientador ou Supervisor": form_data["orientador"],
        "Título": form_data["titulo"],
        "Componente Curricular": form_data["componente"],
        "Anexos": ", ".join(file_links),
    }
    
    # Adicionar na aba "Respostas ao formulário 1"
    append_rows([row_data], sheet_id, range_name="Respostas ao formulário 1")

    # Enviar email de notificação formatado
    recipients = _coerce_recipients(notification_recipients)
    if recipients:
        # Formatar data/hora atual
        data_formatada = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
        
        # Formatar anexos com links
        anexos_formatados = "\n".join([
            f"    {idx}. {name}\n       🔗 {link}"
            for idx, (name, link) in enumerate(zip(file_names, file_links), 1)
        ])
        
        # Emoji para componente
        componente_emoji = "📘" if "Plano" in form_data["componente"] else "📗"
        
        # Adicionar email do aluno
        aluno_email = form_data["email"]
        if aluno_email and aluno_email not in recipients:
            recipients.append(aluno_email)
        
        subject = f"✅ Nova Submissão de Estágio Recebida - {componente_simplificado}"
        body = f"""\
Olá,

Uma nova resposta foi registrada no formulário de Estágio.

📅 Data: {data_formatada}
{componente_emoji} Componente: {form_data['componente']}
🎓 Nome: {form_data['nome']}
🔢 Matrícula: {form_data['matricula']}
📧 E-mail: {form_data['email']}
📌 Turma: {form_data['turma']}
👨‍🏫 Orientador/Supervisor: {form_data['orientador']}
📄 Título: {form_data['titulo']}

📎 Anexos ({len(file_names)} arquivo(s)): 
{anexos_formatados}

🔗 Você pode acessar os anexos através dos links fornecidos.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Sistema de Automação da FASI
"""
        
        send_email_with_attachments(subject, body, recipients)

    return {
        "nome": form_data["nome"],
        "email": form_data["email"],
        "turma": form_data["turma"],
        "matricula": form_data["matricula"],
        "componente": form_data["componente"],
        "orientador": form_data["orientador"],
        "titulo": form_data["titulo"],
        "file_ids": file_ids,
        "file_links": file_links,
        "total_files": len(file_names),
    }
