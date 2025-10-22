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
) -> AccSubmission:
    """Processa submissões ACC de forma RÁPIDA (sem espera de IA).
    
    Fluxo:
    1. Upload para Drive (imediato)
    2. Salvamento no Sheets (imediato)
    3. Email de confirmação (imediato)
    4. Processamento IA em background (thread separada)
    5. Email adicional quando IA concluir (assíncrono)
    
    O usuário NÃO espera o processamento IA.
    """
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

    # Processar PDF com IA em BACKGROUND (thread separada)
    # Criar cópia do arquivo em bytes para processar em background
    uploaded_file.seek(0)
    file_bytes = uploaded_file.read()
    
    def process_ia_background():
        """Função para processar IA em background."""
        try:
            print(f"\n🤖 [BACKGROUND] Iniciando processamento IA para matrícula {sanitized['registration']}...")
            
            # Salvar PDF temporariamente
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(file_bytes)
                tmp_pdf_path = tmp_file.name
            
            # Processar com IA
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
            
            print(f"✅ [BACKGROUND] Processamento IA concluído: {total_carga_horaria}")
            
            # Enviar email ÚNICO com resultado da IA
            if recipients and total_carga_horaria:
                from datetime import datetime
                data_formatada = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
                
                # Formatar anexos com links
                anexos_formatados = "\n".join([
                    f"    • {name}: {link}"
                    for name, link in zip(file_names_for_email, file_links_for_email)
                ])
                
                subject_ia = "✅ Análise de ACC Concluída"
                body_ia = f"""\
Olá,

Sua submissão de Atividades Curriculares Complementares (ACC) foi processada com sucesso!

📅 Data: {data_formatada}
🎓 Nome: {sanitized['name']}
🔢 Matrícula: {sanitized['registration']}
📧 E-mail: {sanitized['email']}
📌 Turma: {sanitized['class_group']}

📎 Anexos enviados:
{anexos_formatados}

🤖 Análise com IA:
⏱️  Carga Horária Total: {total_carga_horaria}

� Arquivo com análise detalhada está anexado.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Sistema de Automação da FASI
"""
                attachments = [txt_path] if txt_path else None
                send_email_with_attachments(subject_ia, body_ia, recipients, attachments)
                
                print(f"✅ [BACKGROUND] Email com análise IA enviado para {len(recipients)} destinatário(s)")
        
        except Exception as e:
            print(f"⚠️ [BACKGROUND] Erro no processamento com IA: {str(e)}")
            # Enviar email ÚNICO informando que IA falhou (análise manual necessária)
            if recipients:
                from datetime import datetime
                data_formatada = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
                
                # Formatar anexos com links
                anexos_formatados = "\n".join([
                    f"    • {name}: {link}"
                    for name, link in zip(file_names_for_email, file_links_for_email)
                ])
                
                subject_erro = "⚠️ Submissão de ACC Recebida - Análise Manual Necessária"
                body_erro = f"""\
Olá,

Sua submissão de Atividades Curriculares Complementares (ACC) foi recebida com sucesso!

📅 Data: {data_formatada}
🎓 Nome: {sanitized['name']}
🔢 Matrícula: {sanitized['registration']}
📧 E-mail: {sanitized['email']}
📌 Turma: {sanitized['class_group']}

📎 Anexos enviados:
{anexos_formatados}

⚠️ Status: O processamento automático com IA não pôde ser concluído.
A coordenação fará a análise manual dos seus certificados.

🔗 Você pode acessar os anexos através dos links fornecidos.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Sistema de Automação da FASI
"""
                send_email_with_attachments(subject_erro, body_erro, recipients, None)
    
    # Adicionar dados na planilha IMEDIATAMENTE (sem carga horária por enquanto)
    row_data = {
        "Nome": sanitized["name"],
        "Matrícula": sanitized["registration"],
        "Email": sanitized["email"],
        "Turma": sanitized["class_group"],
        "Arquivos": ", ".join(file_links),
    }
    
    append_rows([row_data], sheet_id)

    # Preparar lista de destinatários para o email final (com resultado IA)
    recipients = _coerce_recipients(notification_recipients)
    if recipients:
        # Adicionar email do aluno aos destinatários
        aluno_email = sanitized["email"]
        if aluno_email and aluno_email not in recipients:
            recipients.append(aluno_email)
    
    # Variáveis para usar no background
    file_names_for_email = file_names.copy()
    file_links_for_email = file_links.copy()
    
    # Iniciar thread em background (email será enviado APENAS após processamento IA)
    import threading
    thread = threading.Thread(target=process_ia_background, daemon=True)
    thread.start()
    print(f"🚀 Thread de processamento IA iniciada em background (Thread ID: {thread.ident})")

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


def process_plano_submission(
    form_data: Dict[str, Any],
    uploaded_files: list[Any],
) -> Dict[str, Any]:
    """Processa submissões de Plano de Ensino consolidando fluxo Drive/Sheets/E-mail.
    
    Args:
        form_data: Dados do formulário contendo:
            - docente: Nome do docente responsável
            - semestre: Semestre (ex: "2025.4", "2026.1")
        uploaded_files: Lista de arquivos PDF/DOC para upload
        
    Returns:
        Dicionário com informações do processamento
    """
    from datetime import datetime
    import streamlit as st
    
    if not uploaded_files or len(uploaded_files) == 0:
        raise ValueError("Pelo menos um arquivo é obrigatório.")

    required_fields = ["docente", "semestre"]
    missing = [field for field in required_fields if not str(form_data.get(field, "")).strip()]
    if missing:
        raise ValueError(f"Campos obrigatórios ausentes: {', '.join(missing)}")

    # Carregar configurações de plano de ensino
    try:
        drive_folder_id = st.secrets["plano"]["drive_folder_id"]
        sheet_id = st.secrets["plano"]["sheet_id"]
        notification_recipients = st.secrets["plano"].get("notification_recipients", [])
    except (KeyError, FileNotFoundError) as e:
        raise ValueError("Configurações de Plano de Ensino não encontradas em secrets.toml") from e

    prepared_files = list(prepare_files(uploaded_files))
    
    if not prepared_files:
        raise ValueError("Nenhum arquivo válido para upload.")

    # Upload com estrutura hierárquica: Semestre / Arquivos
    # A pasta do semestre será criada automaticamente
    uploaded_files_info = upload_files(
        prepared_files, 
        drive_folder_id,
        componente=form_data['semestre']  # Criar pasta com nome do semestre
    )
    
    # Extrair informações dos arquivos
    file_ids = [f['id'] for f in uploaded_files_info]
    file_links = [f['webViewLink'] for f in uploaded_files_info]
    file_names = [f['name'] for f in uploaded_files_info]

    # Adicionar dados na planilha
    row_data = {
        "Nome do Docente Responsável": form_data["docente"],
        "Semestre": form_data["semestre"],
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
        
        subject = f"✅ Novo Plano de Ensino Recebido - Semestre {form_data['semestre']}"
        body = f"""\
Olá,

Um novo plano de ensino foi registrado no sistema.

📅 Data: {data_formatada}
📚 Semestre: {form_data['semestre']}
👨‍🏫 Docente Responsável: {form_data['docente']}

📎 Anexos ({len(file_names)} arquivo(s)): 
{anexos_formatados}

🔗 Você pode acessar os anexos através dos links fornecidos.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Sistema de Automação da FASI
"""
        
        send_email_with_attachments(subject, body, recipients)

    return {
        "docente": form_data["docente"],
        "semestre": form_data["semestre"],
        "file_ids": file_ids,
        "file_links": file_links,
        "total_files": len(file_names),
    }


def process_projetos_submission(
    form_data: Dict[str, Any],
    uploaded_files: list,
) -> Dict[str, Any]:
    """
    Processa submissão do formulário de Projetos.
    
    Args:
        form_data: Dados do formulário (docente, pareceristas, projeto, etc.)
        uploaded_files: Lista de arquivos enviados
        
    Returns:
        Dict contendo IDs e links dos arquivos enviados
    """
    from src.utils.PDFGenerator import gerar_pdf_projetos, gerar_pdf_declaracao_projeto
    
    # Validar campos obrigatórios
    required_fields = [
        "docente", "parecerista1", "parecerista2", "nome_projeto",
        "carga_horaria", "edital", "natureza", "ano_edital", "solicitacao"
    ]
    for field in required_fields:
        if not form_data.get(field):
            raise ValueError(f"Campo obrigatório ausente: {field}")
    
    # Carregar configurações de secrets
    drive_folder_id = st.secrets["projetos"]["drive_folder_id"]
    sheet_id = st.secrets["projetos"]["sheet_id"]
    notification_recipients = _coerce_recipients(
        st.secrets["projetos"].get("notification_recipients", [])
    )
    pareceristas_str = st.secrets["projetos"].get("pareceristas", "")
    
    # Parse do dicionário de pareceristas
    pareceristas_dict = {}
    if pareceristas_str:
        pares = pareceristas_str.split(",")
        for par in pares:
            if ":" in par:
                nome, email = par.split(":", 1)
                pareceristas_dict[nome.strip()] = email.strip()
    
    # ===============================================
    # GERAR PDFs: Parecer e Declaração
    # ===============================================
    # Preparar dados para o gerador de PDF (formato esperado: lista)
    # Os métodos esperam: [timestamp, docente, parecerista1, parecerista2, projeto, 
    #                      carga_horaria, edital, natureza, ano_edital, solicitacao]
    from datetime import datetime
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    pdf_data = [
        timestamp,
        form_data["docente"],
        form_data["parecerista1"],
        form_data["parecerista2"],
        form_data["nome_projeto"],
        form_data["carga_horaria"],
        form_data["edital"],
        form_data["natureza"],
        form_data["ano_edital"],
        form_data["solicitacao"],
    ]
    
    # Gerar PDFs
    pdf_parecer_path = gerar_pdf_projetos(pdf_data)
    pdf_declaracao_path = gerar_pdf_declaracao_projeto(pdf_data)
    
    # ===============================================
    # PREPARAR ARQUIVOS PARA UPLOAD
    # ===============================================
    # Coletar nomes dos arquivos enviados pelo usuário
    user_file_names = [f.name for f in uploaded_files if hasattr(f, 'name')]
    
    # Criar lista combinada: arquivos do usuário + PDFs gerados
    all_files_to_upload = list(uploaded_files)  # Converter para lista se necessário
    
    # Adicionar PDFs gerados à lista de arquivos
    # Criar objetos BytesIO para os PDFs que serão tratados como arquivos
    from io import BytesIO
    
    # Ler PDF do parecer
    with open(pdf_parecer_path, "rb") as f:
        pdf_parecer_content = f.read()
    
    pdf_parecer_file = BytesIO(pdf_parecer_content)
    pdf_parecer_file.name = os.path.basename(pdf_parecer_path)
    pdf_parecer_file.type = "application/pdf"
    
    # Ler PDF da declaração
    with open(pdf_declaracao_path, "rb") as f:
        pdf_declaracao_content = f.read()
    
    pdf_declaracao_file = BytesIO(pdf_declaracao_content)
    pdf_declaracao_file.name = os.path.basename(pdf_declaracao_path)
    pdf_declaracao_file.type = "application/pdf"
    
    # Adicionar PDFs à lista de upload
    all_files_to_upload.append(pdf_parecer_file)
    all_files_to_upload.append(pdf_declaracao_file)
    
    # Lista de todos os nomes de arquivos
    all_file_names = user_file_names + [
        os.path.basename(pdf_parecer_path),
        os.path.basename(pdf_declaracao_path)
    ]
    
    # ===============================================
    # UPLOAD NO GOOGLE DRIVE
    # ===============================================
    # Estrutura: Edital / Ano do Edital / Nome do Docente / Solicitação
    uploaded_files_info = upload_files(
        all_files_to_upload,
        drive_folder_id,
        edital=form_data["edital"],
        ano_edital=form_data["ano_edital"],
        docente=form_data["docente"],
        solicitacao=form_data["solicitacao"],
    )
    
    # Extrair informações dos arquivos
    file_ids = [f['id'] for f in uploaded_files_info]
    file_links = [f['webViewLink'] for f in uploaded_files_info]
    
    # ===============================================
    # SALVAR NO GOOGLE SHEETS
    # ===============================================
    # Formato: Carimbo, Docente, Parecerista1, Parecerista2, Nome Projeto,
    #          Carga Horária, Edital, Natureza, Ano Edital, Solicitação, Anexos
    anexos_formatados = "\n".join(
        f"{name}: {link}" for name, link in zip(all_file_names, file_links)
    )
    
    row_data = {
        "Carimbo de data/hora": timestamp,
        "Nome do Docente Responsável": form_data["docente"],
        "Nome do Parecerista 1": form_data["parecerista1"],
        "Nome do Parecerista 2": form_data["parecerista2"],
        "Nome do Projeto": form_data["nome_projeto"],
        "Carga Horária": form_data["carga_horaria"],
        "Edital": form_data["edital"],
        "Natureza": form_data["natureza"],
        "Ano do Edital": form_data["ano_edital"],
        "Solicitação": form_data["solicitacao"],
        "Anexos": anexos_formatados,
    }
    
    append_rows([row_data], sheet_id)
    
    # ===============================================
    # ENVIAR E-MAILS
    # ===============================================
    # Destinatários: notification_recipients + docente + pareceristas (via pareceristas_dict)
    recipients = list(notification_recipients)
    
    # Adicionar email do docente se disponível
    docente_email = pareceristas_dict.get(form_data["docente"])
    if docente_email and docente_email not in recipients:
        recipients.append(docente_email)
    
    # Adicionar email do Parecerista 1 se disponível
    parecerista1_email = pareceristas_dict.get(form_data["parecerista1"])
    if parecerista1_email and parecerista1_email not in recipients:
        recipients.append(parecerista1_email)
    
    # Adicionar email do Parecerista 2 se disponível
    parecerista2_email = pareceristas_dict.get(form_data["parecerista2"])
    if parecerista2_email and parecerista2_email not in recipients:
        recipients.append(parecerista2_email)
    
    # Preparar anexos de email (PDFs gerados)
    email_attachments = [
        pdf_parecer_path,
        pdf_declaracao_path,
    ]
    
    # Assunto e corpo do email
    subject = f"Novo Projeto Submetido - {form_data['nome_projeto']}"
    body = f"""
Prezado(a),

Um novo projeto foi submetido através do Sistema de Automação da FASI.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 INFORMAÇÕES DO PROJETO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👨‍🏫 Docente Responsável: {form_data['docente']}

📝 Pareceristas:
   • Parecerista 1: {form_data['parecerista1']}
   • Parecerista 2: {form_data['parecerista2']}

📊 Projeto: {form_data['nome_projeto']}

⏱️ Carga Horária: {form_data['carga_horaria']} horas

📢 Edital: {form_data['edital']}

🎯 Natureza: {form_data['natureza']}

📅 Ano do Edital: {form_data['ano_edital']}

📋 Tipo de Solicitação: {form_data['solicitacao']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📎 ANEXOS ({len(all_file_names)} arquivo(s))
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{anexos_formatados}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 DOCUMENTOS GERADOS AUTOMATICAMENTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Parecer do Projeto (PDF anexado)
✅ Declaração do Projeto (PDF anexado)

Os documentos gerados foram anexados a este e-mail e também salvos no Google Drive junto com os demais anexos.

🔗 Você pode acessar todos os documentos através dos links fornecidos acima.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Sistema de Automação da FASI
"""
    
    # Enviar email com anexos (PDFs gerados)
    send_email_with_attachments(subject, body, recipients, attachments=email_attachments)
    
    # Limpar arquivos temporários
    try:
        os.remove(pdf_parecer_path)
        os.remove(pdf_declaracao_path)
    except:
        pass
    
    return {
        "docente": form_data["docente"],
        "nome_projeto": form_data["nome_projeto"],
        "file_ids": file_ids,
        "file_links": file_links,
        "total_files": len(all_file_names),
        "pdf_parecer": os.path.basename(pdf_parecer_path),
        "pdf_declaracao": os.path.basename(pdf_declaracao_path),
    }

