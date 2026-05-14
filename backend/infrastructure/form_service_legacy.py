from __future__ import annotations

from typing import Any, Dict, Iterable
import io
import os
import tempfile
import unicodedata

from backend.config.settings import settings
from backend.infrastructure.database.schemas_legacy import AccSubmission
from backend.infrastructure.email.service import send_notification, send_email_with_attachments
from backend.infrastructure.file_processing.processor import prepare_files, sanitize_submission
from backend.infrastructure.google.drive import upload_files
from backend.infrastructure.google.sheets import append_rows  # Mantido para compatibilidade temporária
from backend.utils.datetime_utils import format_local_datetime
from backend.infrastructure.database.repository import (
    save_tcc_submission,
    save_acc_submission,
    save_projetos_submission,
    save_plano_ensino_submission,
    save_estagio_submission,
    save_social_submission,
)



def _coerce_recipients(recipients: Iterable[str] | str | None) -> list[str]:
    if recipients is None:
        return []
    if isinstance(recipients, str):
        return [email.strip() for email in recipients.split(",") if email.strip()]
    return [email.strip() for email in recipients if email.strip()]


def _parse_name_email_map(raw_value: str | None) -> dict[str, str]:
    parsed: dict[str, str] = {}
    if not raw_value:
        return parsed

    for item in raw_value.split(","):
        if ":" not in item:
            continue
        name, email = item.split(":", 1)
        name = name.strip()
        email = email.strip()
        if name and email:
            parsed[name] = email
    return parsed


def _is_blank(value: Any) -> bool:
    """Retorna True para valores ausentes/vazios usados em validação."""
    if value is None:
        return True
    return not str(value).strip()


def _normalize_filename(value: str) -> str:
    """Normaliza nomes de arquivo para comparação tolerante a acentos e símbolos."""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_only.lower().replace("_", " ").replace("-", " ").split())


def _normalize_person_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_only.casefold().split())


def _find_email_by_name(name: str, name_email_map: dict[str, str]) -> str | None:
    if name in name_email_map:
        return name_email_map[name]

    normalized_name = _normalize_person_name(name)
    for mapped_name, email in name_email_map.items():
        if _normalize_person_name(mapped_name) == normalized_name:
            return email
    return None


def validate_tcc2_uploaded_files(uploaded_files: Iterable[Any]) -> str | None:
    """Valida os anexos obrigatórios do TCC 2.

    Aceita dois formatos:
    - 2 PDFs: TCC Final + um PDF de autorização/autoria
    - 3 PDFs separados também continuam aceitos
    """
    files = list(uploaded_files or [])
    if len(files) < 2:
        return (
            "TCC 2 requer no mínimo 2 arquivos: "
            "1 PDF com Declaração de Autoria + Termo de Autorização "
            "(ou esses 2 documentos separados) e 1 PDF do TCC Final."
        )

    normalized_names = [_normalize_filename(getattr(file, "name", "")) for file in files]

    has_tcc_final = any(
        ("tcc" in name and "final" in name) or "versao final" in name
        for name in normalized_names
    )
    has_declaracao = any("declaracao" in name and "autoria" in name for name in normalized_names)
    has_termo = any("termo" in name and "autorizacao" in name for name in normalized_names)
    has_authorization_doc = has_declaracao or has_termo
    has_combined_doc = any(
        "declaracao" in name and "autoria" in name and "termo" in name and "autorizacao" in name
        for name in normalized_names
    )

    if len(files) >= 3:
        return None

    if has_combined_doc and has_tcc_final:
        return None

    if has_authorization_doc and has_tcc_final:
        return None

    return (
        "Para TCC 2, envie o PDF do TCC Final e pelo menos um PDF de "
        "Declaração de Autoria ou Termo de Autorização."
    )


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
    if uploaded_file is None:
        raise ValueError("Arquivo obrigatório não informado.")

    required_fields = ["name", "registration", "email", "class_group", "polo", "periodo"]
    missing = [field for field in required_fields if _is_blank(form_data.get(field, ""))]
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
            print(f"🔄 [BACKGROUND] Iniciando processamento IA para {sanitized['name']} ({sanitized['registration']})")
            
            from backend.infrastructure.file_processing.acc_processor import processar_certificados_acc
            
            resultado = processar_certificados_acc(
                pdf_path=tmp_pdf_path,
                matricula=sanitized["registration"],
                nome=sanitized["name"]
            )
            
            # Verificar se houve erro no processamento
            status_processamento = resultado.get("status", "desconhecido")
            txt_path = resultado.get("txt_path")
            total_carga_horaria = resultado.get("total_geral")
            
            # Limpar arquivo temporário
            try:
                os.remove(tmp_pdf_path)
            except Exception as e:
                print(f"⚠️ [BACKGROUND] Erro ao remover arquivo temporário: {e}")
            
            if status_processamento == "erro":
                print(f"❌ [BACKGROUND] Erro no processamento IA: {resultado.get('erro', 'Erro desconhecido')}")
                print(f"   Tipo do erro: {resultado.get('tipo_erro', 'N/A')}")
                total_carga_horaria = f"❌ ERRO: {resultado.get('erro', 'Processamento falhou')}"
            else:
                print(f"✅ [BACKGROUND] Processamento IA concluído: {total_carga_horaria}")
            
            # Enviar email ÚNICO com resultado da IA
            if recipients and total_carga_horaria:
                data_formatada = format_local_datetime()
                
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
🏫 Polo: {sanitized.get('polo', form_data.get('polo', ''))}
🗓️ Período: {sanitized.get('periodo', form_data.get('periodo', ''))}

📎 Anexos enviados:
{anexos_formatados}

🤖 Análise com IA:
⏱️  Carga Horária Total: {total_carga_horaria.replace("TOTAL GERAL:", "").strip()}

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
                data_formatada = format_local_datetime()
                
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
🏫 Polo: {sanitized.get('polo', form_data.get('polo', ''))}
🗓️ Período: {sanitized.get('periodo', form_data.get('periodo', ''))}

📎 Anexos enviados:
{anexos_formatados}

⚠️ Status: O processamento automático com IA não pôde ser concluído.
A coordenação fará a análise manual dos seus certificados.

🔗 Você pode acessar os anexos através dos links fornecidos.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Sistema de Automação da FASI
"""
                send_email_with_attachments(subject_erro, body_erro, recipients, None)
    
    # Salvar no banco de dados
    db_data = {
        "name": sanitized["name"],
        "registration": sanitized["registration"],
        "email": sanitized["email"],
        "class_group": sanitized["class_group"],
        "polo": sanitized.get("polo", form_data.get("polo", "")),
        "periodo": sanitized.get("periodo", form_data.get("periodo", "")),
        "semester": sanitized.get("semester", ""),
        "file_link": ", ".join(file_links) if file_links else None,
        "drive_file_id": file_ids[0] if file_ids else None,
    }

    submission_id = save_acc_submission(db_data)

    # Salvar no Google Sheets
    try:
        if sheet_id:
            sheet_row = {
                "Nome": sanitized["name"],
                "Matrícula": sanitized["registration"],
                "Email": sanitized["email"],
                "Turma": sanitized["class_group"],
                "Polo": sanitized.get("polo", form_data.get("polo", "")),
                "Período": sanitized.get("periodo", form_data.get("periodo", "")),
                "Anexos": ", ".join(file_links),
            }
            append_rows([sheet_row], sheet_id)
    except Exception as exc:
        print(f"⚠️ Erro ao salvar ACC no Sheets: {exc}")

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
    if not uploaded_files or len(uploaded_files) == 0:
        raise ValueError("Pelo menos um arquivo é obrigatório.")

    required_fields = ["name", "registration", "email", "class_group", "polo", "periodo", "orientador", "titulo", "componente"]
    missing = [field for field in required_fields if _is_blank(form_data.get(field, ""))]
    if missing:
        raise ValueError(f"Campos obrigatórios ausentes: {', '.join(missing)}")

    # Validar quantidade de arquivos para TCC 2
    componente = form_data.get("componente", "").strip()
    if componente == "TCC 2":
        tcc2_error = validate_tcc2_uploaded_files(uploaded_files)
        if tcc2_error:
            raise ValueError(tcc2_error)

    sanitized = sanitize_submission(form_data)
    prepared_files = list(prepare_files(uploaded_files))
    
    if not prepared_files:
        raise ValueError("Nenhum arquivo válido para upload.")

    # Upload com estrutura hierárquica: TCC 1 ou TCC 2 / Turma / Nome do Aluno
    # Importar função auxiliar para criar pastas hierárquicas
    from backend.infrastructure.google.drive import upload_files_tcc
    
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

    # Formatar anexos para salvar no banco
    anexos_formatados = "\n".join(
        f"{name}: {link}" for name, link in zip(file_names, file_links)
    )

    # Salvar no banco de dados
    db_data = {
        "name": sanitized["name"],
        "registration": sanitized["registration"],
        "email": sanitized["email"],
        "class_group": sanitized["class_group"],
        "polo": sanitized.get("polo", form_data.get("polo", "")),
        "periodo": sanitized.get("periodo", form_data.get("periodo", "")),
        "orientador": sanitized.get("orientador", form_data.get("orientador", "")),
        "titulo": sanitized.get("titulo", form_data.get("titulo", "")),
        "componente": componente,
        "anexos": anexos_formatados,
        "drive_folder_id": drive_folder_id,
    }
    
    submission_id = save_tcc_submission(db_data)

    # Salvar no Google Sheets
    try:
        if sheet_id:
            sheet_row = {
                "Nome": sanitized["name"],
                "Email": sanitized["email"],
                "Turma": sanitized["class_group"],
                "Matrícula": sanitized["registration"],
                "Polo": sanitized.get("polo", form_data.get("polo", "")),
                "Orientador": form_data.get("orientador", ""),
                "Título": form_data.get("titulo", ""),
                "Componente": componente,
                "Arquivos": ", ".join(file_links),
            }
            append_rows([sheet_row], sheet_id)
    except Exception as exc:
        print(f"⚠️ Erro ao salvar TCC no Sheets: {exc}")

    # Enviar email de notificação formatado
    recipients = _coerce_recipients(notification_recipients)
    if recipients:
        # Formatar data/hora atual
        data_formatada = format_local_datetime()

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
🏫 Polo: {sanitized.get('polo', form_data.get('polo', ''))}
🗓️ Período: {sanitized.get('periodo', form_data.get('periodo', ''))}
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
        "polo": sanitized.get("polo", form_data.get("polo", "")),
        "periodo": sanitized.get("periodo", form_data.get("periodo", "")),
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
    if not uploaded_files or len(uploaded_files) == 0:
        raise ValueError("Pelo menos um arquivo é obrigatório.")

    required_fields = ["nome", "email", "turma", "polo", "periodo", "matricula", "orientador", "titulo", "componente"]
    missing = [field for field in required_fields if _is_blank(form_data.get(field, ""))]
    if missing:
        raise ValueError(f"Campos obrigatórios ausentes: {', '.join(missing)}")

    drive_folder_id = settings.estagio_folder_id
    sheet_id = settings.estagio_sheet_id
    notification_recipients = _coerce_recipients(settings.estagio_recipients or settings.destinatarios or [])

    prepared_files = list(prepare_files(uploaded_files))
    
    if not prepared_files:
        raise ValueError("Nenhum arquivo válido para upload.")

    # Upload com estrutura hierárquica: Componente Curricular / Turma / Arquivos
    # Extrair componente simplificado (Plano de Estágio ou Relatório Final)
    componente_simplificado = form_data["componente"].split(" (")[0]  # "Plano de Estágio" ou "Relatório Final"
    
    uploaded_files_info = upload_files(
        prepared_files, 
        drive_folder_id,
        matricula=form_data['nome'],#Insirar Nome no ultimo nivel de pasta
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
        "Polo": form_data["polo"],
        "Período": form_data["periodo"],
        "Matrícula": form_data["matricula"],
        "Orientador ou Supervisor": form_data["orientador"],
        "Título": form_data["titulo"],
        "Componente Curricular": form_data["componente"],
        "Anexos": ", ".join(file_links),
    }
    
    # Salvar no banco de dados
    anexos_formatados = "\n".join(
        f"{name}: {link}" for name, link in zip(file_names, file_links)
    )
    
    db_data = {
        "nome": form_data["nome"],
        "matricula": form_data["matricula"],
        "email": form_data["email"],
        "turma": form_data["turma"],
        "polo": form_data["polo"],
        "periodo": form_data["periodo"],
        "orientador": form_data["orientador"],
        "titulo": form_data["titulo"],
        "componente": form_data["componente"],
        "anexos": anexos_formatados,
        "drive_folder_id": drive_folder_id,
    }
    
    submission_id = save_estagio_submission(db_data)

    # Salvar no Google Sheets
    try:
        if sheet_id:
            append_rows([row_data], sheet_id)
    except Exception as exc:
        print(f"⚠️ Erro ao salvar Estágio no Sheets: {exc}")

    # Enviar email de notificação formatado
    recipients = _coerce_recipients(notification_recipients)
    if recipients:
        # Formatar data/hora atual
        data_formatada = format_local_datetime()
        
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
🏫 Polo: {form_data['polo']}
🗓️ Período: {form_data['periodo']}
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
        "polo": form_data["polo"],
        "periodo": form_data["periodo"],
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
    if not uploaded_files or len(uploaded_files) == 0:
        raise ValueError("Pelo menos um arquivo é obrigatório.")

    required_fields = ["docente", "semestre"]
    missing = [field for field in required_fields if _is_blank(form_data.get(field, ""))]
    if missing:
        raise ValueError(f"Campos obrigatórios ausentes: {', '.join(missing)}")

    drive_folder_id = settings.plano_folder_id
    notification_recipients = _coerce_recipients(settings.plano_recipients or settings.destinatarios or [])

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
    
    # Salvar no banco de dados
    anexos_formatados = "\n".join(
        f"{name}: {link}" for name, link in zip(file_names, file_links)
    )
    
    db_data = {
        "professor": form_data["docente"],
        "disciplina": form_data.get("disciplina", ""),
        "codigo_disciplina": form_data.get("codigo_disciplina"),
        "periodo_letivo": form_data["semestre"],
        "carga_horaria": form_data.get("carga_horaria"),
        "anexos": anexos_formatados,
        "drive_folder_id": drive_folder_id,
    }
    
    submission_id = save_plano_ensino_submission(db_data)

    # Salvar no Google Sheets
    try:
        plano_sheet_id = settings.plano_sheet_id
        if plano_sheet_id:
            append_rows([row_data], plano_sheet_id)
    except Exception as exc:
        print(f"⚠️ Erro ao salvar Plano de Ensino no Sheets: {exc}")

    # Enviar email de notificação formatado
    recipients = _coerce_recipients(notification_recipients)
    if recipients:
        # Formatar data/hora atual
        data_formatada = format_local_datetime()
        
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
    from backend.utils.PDFGenerator import gerar_pdf_projetos, gerar_pdf_declaracao_projeto
    
    # Validar campos obrigatórios
    required_fields = [
        "docente", "parecerista1", "parecerista2", "nome_projeto",
        "carga_horaria", "edital", "natureza", "ano_edital", "solicitacao"
    ]
    for field in required_fields:
        if not form_data.get(field):
            raise ValueError(f"Campo obrigatório ausente: {field}")
    
    drive_folder_id = settings.projetos_folder_id
    sheet_id = settings.projetos_sheet_id
    notification_recipients = _coerce_recipients(settings.projetos_recipients or settings.destinatarios or [])
    pareceristas_str = settings.pareceristas or os.getenv("PARECERISTAS", "")
    pareceristas_dict = _parse_name_email_map(pareceristas_str)
    
    # ===============================================
    # GERAR PDFs: Parecer e Declaração (exceto para Encerramento)
    # ===============================================
    # Preparar dados para o gerador de PDF (formato esperado: lista)
    # Os métodos esperam: [timestamp, docente, parecerista1, parecerista2, projeto, 
    #                      carga_horaria, edital, natureza, ano_edital, solicitacao]
    timestamp = format_local_datetime("%d/%m/%Y %H:%M:%S")
    
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
    
    # Gerar PDF do Parecer (sempre)
    pdf_parecer_path = gerar_pdf_projetos(pdf_data)
    
    # Gerar PDF da Declaração apenas se NÃO for Encerramento
    pdf_declaracao_path = None
    is_encerramento = form_data["solicitacao"].lower() == "encerramento"
    if not is_encerramento:
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
    
    # Adicionar PDF do parecer à lista de upload
    all_files_to_upload.append(pdf_parecer_file)
    
    # Lista de todos os nomes de arquivos (começa com arquivos do usuário + parecer)
    all_file_names = user_file_names + [os.path.basename(pdf_parecer_path)]
    
    # Ler e adicionar PDF da declaração apenas se foi gerado (não é Encerramento)
    if pdf_declaracao_path:
        with open(pdf_declaracao_path, "rb") as f:
            pdf_declaracao_content = f.read()
        
        pdf_declaracao_file = BytesIO(pdf_declaracao_content)
        pdf_declaracao_file.name = os.path.basename(pdf_declaracao_path)
        pdf_declaracao_file.type = "application/pdf"
        
        all_files_to_upload.append(pdf_declaracao_file)
        all_file_names.append(os.path.basename(pdf_declaracao_path))
    
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
    
    # Salvar no banco de dados
    db_data = {
        "docente": form_data["docente"],
        "parecerista1": form_data["parecerista1"],
        "parecerista2": form_data["parecerista2"],
        "nome_projeto": form_data["nome_projeto"],
        "carga_horaria": form_data["carga_horaria"],
        "edital": form_data["edital"],
        "natureza": form_data["natureza"],
        "ano_edital": form_data["ano_edital"],
        "solicitacao": form_data["solicitacao"],
        "anexos": anexos_formatados,
        "pdf_parecer": os.path.basename(pdf_parecer_path),
        "pdf_declaracao": os.path.basename(pdf_declaracao_path) if pdf_declaracao_path else None,
        "drive_folder_id": drive_folder_id,
    }
    
    submission_id = save_projetos_submission(db_data)

    # Salvar no Google Sheets
    try:
        if sheet_id:
            append_rows([row_data], sheet_id)
    except Exception as exc:
        print(f"⚠️ Erro ao salvar Projetos no Sheets: {exc}")

    # ===============================================
    # ENVIAR E-MAILS
    # ===============================================
    # Destinatários: notification_recipients + docente + pareceristas (via pareceristas_dict)
    recipients = list(notification_recipients)
    
    # Adicionar email do docente se disponível
    docente_email = _find_email_by_name(form_data["docente"], pareceristas_dict)
    if docente_email and docente_email not in recipients:
        recipients.append(docente_email)
    
    # Adicionar email do Parecerista 1 se disponível
    parecerista1_email = _find_email_by_name(form_data["parecerista1"], pareceristas_dict)
    if parecerista1_email and parecerista1_email not in recipients:
        recipients.append(parecerista1_email)
    
    # Adicionar email do Parecerista 2 se disponível
    parecerista2_email = _find_email_by_name(form_data["parecerista2"], pareceristas_dict)
    if parecerista2_email and parecerista2_email not in recipients:
        recipients.append(parecerista2_email)
    
    # Preparar anexos de email (PDFs gerados)
    email_attachments = [pdf_parecer_path]
    if pdf_declaracao_path:
        email_attachments.append(pdf_declaracao_path)
    
    # Texto de documentos gerados para o corpo do email
    docs_gerados_texto = "✅ Parecer do Projeto (PDF anexado)"
    if pdf_declaracao_path:
        docs_gerados_texto += "\n✅ Declaração do Projeto (PDF anexado)"
    
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

{docs_gerados_texto}

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
        if pdf_declaracao_path:
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
        "pdf_declaracao": os.path.basename(pdf_declaracao_path) if pdf_declaracao_path else None,
    }


# ---------------------------------------------------------------------------
# Submissões JSON (sem arquivo) — Social, Avaliação, Requerimento TCC, Emissão
# ---------------------------------------------------------------------------

def process_social_submission(**kwargs: Any) -> Dict[str, Any]:
    """Salva dados do formulário socioeconômico e envia notificação interna."""
    from backend.infrastructure.database.repository import save_social_submission  # noqa: PLC0415

    submission_id = save_social_submission(kwargs)

    # Salvar no Google Sheets
    try:
        social_sheet_id = settings.social_sheet_id
        if social_sheet_id:
            sheet_row = {
                "Matrícula": kwargs.get("matricula", ""),
                "Periodo": kwargs.get("periodo_referencia", ""),
                "Cor/Etnia": kwargs.get("cor_etnia", ""),
                "PCD": kwargs.get("pcd", ""),
                "Tipo de Deficiência": kwargs.get("tipo_deficiencia", ""),
                "Renda": kwargs.get("renda", ""),
                "Deslocamento": kwargs.get("deslocamento", ""),
                "Trabalho": kwargs.get("trabalho", ""),
                "Assistência Estudantil": kwargs.get("assistencia_estudantil", ""),
                "Saúde Mental": kwargs.get("saude_mental", ""),
                "Estresse": kwargs.get("estresse", ""),
                "Acompanhamento": kwargs.get("acompanhamento", ""),
                "Escolaridade Pai": kwargs.get("escolaridade_pai", ""),
                "Escolaridade Mãe": kwargs.get("escolaridade_mae", ""),
                "Qtd Computador": kwargs.get("qtd_computador", ""),
                "Qtd Celular": kwargs.get("qtd_celular", ""),
                "Computador Próprio": kwargs.get("computador_proprio", ""),
                "Gasto Internet": kwargs.get("gasto_internet", ""),
                "Acesso Internet": kwargs.get("acesso_internet", ""),
                "Tipo Moradia": kwargs.get("tipo_moradia", ""),
            }
            append_rows([sheet_row], social_sheet_id)
    except Exception as exc:
        print(f"⚠️ Erro ao salvar Social no Sheets: {exc}")

    try:
        recipients = _coerce_recipients(settings.social_recipients or settings.destinatarios)
        if recipients:
            subject = f"[FasiTech] Nova submissão social — Matrícula {kwargs.get('matricula', '?')}"
            body = (
                f"Nova resposta do formulário socioeconômico recebida.\n\n"
                f"Matrícula: {kwargs.get('matricula')}\n"
                f"Período: {kwargs.get('periodo_referencia')}\n"
                f"Polo: {kwargs.get('polo')}\n"
            )
            send_notification(subject, body, recipients)
    except Exception as exc:
        print(f"⚠️ Erro ao notificar submissão social: {exc}")

    return {"id": submission_id}


def process_avaliacao_gestao_submission(**kwargs: Any) -> Dict[str, Any]:
    """Salva avaliação de gestão (anônima) no banco de dados."""
    from backend.infrastructure.database.repository import save_avaliacao_gestao_submission  # noqa: PLC0415

    # Mapeia nomes snake_case do schema para os nomes capitalizados esperados pelo repository
    key_map = {
        "q1_transparencia": "Q1_Transparencia", "q1_valor": "Q1_Valor",
        "q2_comunicacao": "Q2_Comunicacao", "q2_valor": "Q2_Valor",
        "q3_acessibilidade": "Q3_Acessibilidade", "q3_valor": "Q3_Valor",
        "q4_inclusao": "Q4_Inclusao", "q4_valor": "Q4_Valor",
        "q5_planejamento": "Q5_Planejamento", "q5_valor": "Q5_Valor",
        "q6_recursos": "Q6_Recursos", "q6_valor": "Q6_Valor",
        "q7_eficiencia": "Q7_Eficiencia", "q7_valor": "Q7_Valor",
        "q8_suporte": "Q8_Suporte", "q8_valor": "Q8_Valor",
        "q9_extracurricular": "Q9_Extracurricular", "q9_valor": "Q9_Valor",
        "q10_melhorias": "Q10_Melhorias",
        "q11_outras_questoes": "Q11_Outras_Questoes",
    }
    data = {key_map.get(k, k): v for k, v in kwargs.items()}
    submission_id = save_avaliacao_gestao_submission(data)
    return {"id": submission_id}


def process_requerimento_tcc_submission(**kwargs: Any) -> Dict[str, Any]:
    """Salva requerimento de defesa de TCC e envia notificação aos envolvidos."""
    from backend.infrastructure.database.repository import save_requerimento_tcc_submission  # noqa: PLC0415

    submission_id = save_requerimento_tcc_submission(kwargs)

    try:
        recipients = _coerce_recipients(settings.requerimento_tcc_recipients or settings.destinatarios)
        aluno_email = kwargs.get("email")
        all_recipients = list({aluno_email, *recipients} - {None, ""}) if aluno_email else recipients

        if all_recipients:
            subject = f"[FasiTech] Requerimento de TCC — {kwargs.get('nome_aluno', '?')}"
            body = (
                f"Novo requerimento de defesa de TCC recebido.\n\n"
                f"Aluno(a): {kwargs.get('nome_aluno')}\n"
                f"Matrícula: {kwargs.get('matricula')}\n"
                f"Orientador(a): {kwargs.get('orientador')}\n"
                f"Título: {kwargs.get('titulo_trabalho')}\n"
                f"Modalidade: {kwargs.get('modalidade')}\n"
                f"Data de defesa: {kwargs.get('data_defesa', 'A definir')}\n"
            )
            send_notification(subject, body, all_recipients)
    except Exception as exc:
        print(f"⚠️ Erro ao notificar requerimento TCC: {exc}")

    return {"id": submission_id}


def process_emissao_documentos_submission(**kwargs: Any) -> Dict[str, Any]:
    """Registra solicitação de emissão de documento e notifica o setor responsável."""
    recipients = _coerce_recipients(settings.destinatarios or [])
    nome = kwargs.get("nome", "")
    matricula = kwargs.get("matricula", "")
    email_aluno = kwargs.get("email", "")
    tipo_doc = kwargs.get("tipo_documento", "")
    polo = kwargs.get("polo", "")

    all_recipients = list({email_aluno, *recipients} - {None, ""}) if email_aluno else recipients

    try:
        if all_recipients:
            subject = f"[FasiTech] Solicitação de documento — {nome}"
            body = (
                f"Nova solicitação de emissão de documento.\n\n"
                f"Nome: {nome}\n"
                f"Matrícula: {matricula}\n"
                f"E-mail: {email_aluno}\n"
                f"Tipo de documento: {tipo_doc}\n"
                f"Polo: {polo}\n\n"
                f"Acesse o sistema para processar a solicitação."
            )
            send_notification(subject, body, all_recipients)
    except Exception as exc:
        print(f"⚠️ Erro ao notificar emissão de documentos: {exc}")

    return {"id": 0, "tipo_documento": tipo_doc}
