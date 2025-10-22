from __future__ import annotations

import re
import sys
import time
from pathlib import Path
from typing import Any

import streamlit as st

# Adicionar diretório raiz ao PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

LOGO_PATH = Path(__file__).resolve().parents[2] / "resources" / "fasiOficial.png"
MAX_FILE_SIZE_MB = 10


def _load_estagio_settings() -> dict[str, Any]:
    """Carrega configurações de Estágio do secrets.toml."""
    try:
        return {
            "drive_folder_id": st.secrets["estagio"]["drive_folder_id"],
            "sheet_id": st.secrets["estagio"]["sheet_id"],
            "notification_recipients": st.secrets["estagio"].get("notification_recipients", []),
        }
    except (KeyError, FileNotFoundError) as e:
        st.error(
            f"⚠️ Configurações de Estágio não encontradas em secrets.toml.\n\n"
            f"Por favor, configure a seção [estagio] com:\n"
            f"- drive_folder_id\n"
            f"- sheet_id\n"
            f"- notification_recipients"
        )
        raise ValueError("Configurações de Estágio ausentes") from e


def _render_intro() -> None:
    st.markdown(
        """
        <style>
            /* Estilos alinhados com identidade visual institucional */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            
            /* Ocultar sidebar completamente */
            [data-testid="stSidebar"] {
                display: none;
            }
            [data-testid="collapsedControl"] {
                display: none;
            }
            section[data-testid="stSidebar"] {
                display: none !important;
            }
            
            .estagio-hero {
                background: linear-gradient(135deg, #1a0d2e 0%, #2d1650 50%, #4a1d7a 100%);
                border-radius: 16px;
                padding: 36px;
                color: #ffffff;
                margin-bottom: 32px;
                box-shadow: 0 10px 30px rgba(26, 13, 46, 0.25);
                position: relative;
                overflow: hidden;
            }
            
            .estagio-hero::before {
                content: '';
                position: absolute;
                top: -30%;
                right: -5%;
                width: 300px;
                height: 300px;
                background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
                border-radius: 50%;
            }
            
            .estagio-hero h1 {
                font-size: 1.9rem;
                margin-bottom: 16px;
                font-weight: 700;
                text-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            
            .estagio-hero p {
                font-size: 1.05rem;
                line-height: 1.6;
                margin-bottom: 8px;
                opacity: 0.95;
            }
            
            .estagio-card {
                background: #ffffff;
                border-radius: 16px;
                padding: 36px;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
                border: 1px solid #e2e8f0;
                margin-bottom: 24px;
            }
            
            .estagio-required {
                color: #ef4444;
                font-weight: 700;
            }
            
            .info-box {
                background: #dbeafe;
                border-left: 4px solid #3b82f6;
                padding: 16px;
                margin: 20px 0;
                border-radius: 8px;
            }
            
            .info-box p {
                color: #1e40af;
                margin: 4px 0;
                font-size: 0.95rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    # Logo
    if LOGO_PATH.exists():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(str(LOGO_PATH), use_container_width=True)
    
    # Hero Section
    st.markdown(
        """
        <div class="estagio-hero">
            <h1>📋 Formulário de Envio de Documentos de Estágio</h1>
            <p><strong>Referente às disciplinas de Estágio I e Estágio II</strong></p>
            <p>Preencha os campos abaixo e envie os documentos obrigatórios referentes ao seu estágio.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Info Box
    st.markdown(
        """
        <div class="info-box">
            <p><strong>ℹ️ Informações sobre Componente Curricular:</strong></p>
            <p>• <strong>Plano de Estágio</strong> → Refere-se ao <strong>Estágio I</strong></p>
            <p>• <strong>Relatório Final</strong> → Refere-se ao <strong>Estágio II</strong></p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _validate_email(email: str) -> bool:
    """Valida formato de email."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def _validate_turma(turma: str) -> bool:
    """Valida se a turma tem exatamente 4 dígitos numéricos."""
    return bool(re.match(r'^\d{4}$', turma))


def _validate_submission(
    nome: str,
    email: str,
    turma: str,
    matricula: str,
    orientador: str,
    titulo: str,
    componente: str,
    uploaded_files: list,
) -> list[str]:
    """Executa validações básicas antes de enviar ao backend."""
    errors: list[str] = []
    
    # Nome obrigatório
    if not nome.strip():
        errors.append("Nome completo é obrigatório.")
    
    # Email obrigatório e válido
    if not email.strip():
        errors.append("E-mail é obrigatório.")
    elif not _validate_email(email):
        errors.append("E-mail inválido. Use um formato válido (exemplo@dominio.com).")
    
    # Turma obrigatória e formato válido
    if not turma.strip():
        errors.append("Turma é obrigatória.")
    elif not _validate_turma(turma):
        errors.append("Turma deve ter exatamente 4 dígitos numéricos (ex: 2027).")
    
    # Matrícula obrigatória
    if not matricula.strip():
        errors.append("Matrícula é obrigatória.")
    
    # Orientador obrigatório
    if not orientador.strip():
        errors.append("Orientador ou Supervisor é obrigatório.")
    
    # Título obrigatório
    if not titulo.strip():
        errors.append("Título é obrigatório.")
    
    # Componente obrigatório
    if not componente:
        errors.append("Componente Curricular é obrigatório.")
    
    # Arquivos obrigatórios
    if not uploaded_files:
        errors.append("Você deve enviar pelo menos um arquivo.")
    
    # Validar tamanho dos arquivos
    for file in uploaded_files:
        file_size_mb = file.size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            errors.append(
                f"Arquivo '{file.name}' excede o tamanho máximo de {MAX_FILE_SIZE_MB} MB "
                f"(tamanho atual: {file_size_mb:.2f} MB)."
            )
    
    return errors


def _process_estagio_submission(form_data: dict[str, Any], files: list) -> None:
    """Processa submissão do formulário de estágio."""
    from src.services import form_service
    
    # Processar submissão usando serviço centralizado
    form_service.process_estagio_submission(form_data, files)


def render_form() -> None:
    _render_intro()
    
    
    with st.form("formulario_estagio"):
        st.markdown("<span class='estagio-required'>*</span> Todos os campos são obrigatórios", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Dados Pessoais
        st.markdown("### 👤 Dados Pessoais")
        col1, col2 = st.columns(2)
        
        nome = col1.text_input(
            "Nome Completo *",
            placeholder="Seu nome completo",
            help="Digite seu nome completo como consta no SIGAA"
        )
        
        email = col2.text_input(
            "E-mail *",
            placeholder="seuemail@ufpa.br",
            help="Digite um e-mail válido para receber confirmação"
        )
        
        col3, col4 = st.columns(2)
        
        turma = col3.text_input(
            "Turma *",
            placeholder="2027",
            max_chars=4,
            help="Ano de ingresso (4 dígitos numéricos, ex: 2027)"
        )
        
        matricula = col4.text_input(
            "Matrícula *",
            placeholder="202312345",
            help="Sua matrícula no SIGAA"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Informações do Estágio
        st.markdown("### 📚 Informações do Estágio")
        
        orientador = st.text_input(
            "Orientador ou Supervisor *",
            placeholder="Nome completo do orientador ou supervisor",
            help="Nome do professor orientador ou supervisor de estágio"
        )
        
        titulo = st.text_input(
            "Título *",
            placeholder="Título do Plano ou Relatório de Estágio",
            help="Digite o título do documento de estágio"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Componente Curricular
        st.markdown("### 📋 Componente Curricular")
        
        componente = st.radio(
            "Selecione o Componente Curricular *",
            options=["Plano de Estágio (Estágio I)", "Relatório Final (Estágio II)"],
            help="Plano de Estágio = Estágio I | Relatório Final = Estágio II"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Anexos
        st.markdown("### 📎 Anexos")
        st.markdown(
            f"<p style='color: #6b7280; font-size: 0.9rem;'>"
            f"Tamanho máximo por arquivo: <strong>{MAX_FILE_SIZE_MB} MB</strong> | "
            f"Formato: <strong>PDF</strong></p>",
            unsafe_allow_html=True,
        )
        
        uploaded_files = st.file_uploader(
            "Envie os documentos de estágio *",
            type=["pdf"],
            accept_multiple_files=True,
            help=f"Selecione um ou mais arquivos PDF (máximo {MAX_FILE_SIZE_MB} MB cada)"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Botão de envio
        submitted = st.form_submit_button("Enviar Documentos", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Processar submissão
    if submitted:
        errors = _validate_submission(
            nome, email, turma, matricula, orientador, titulo, componente, uploaded_files or []
        )
        
        if errors:
            st.error("**❌ Erros encontrados:**\n\n" + "\n".join(f"• {error}" for error in errors))
        else:
            with st.spinner("Processando envio de documentos de estágio..."):
                try:
                    # Preparar dados do formulário
                    form_data = {
                        "nome": nome.strip(),
                        "email": email.strip().lower(),
                        "turma": turma.strip(),
                        "matricula": matricula.strip(),
                        "orientador": orientador.strip(),
                        "titulo": titulo.strip(),
                        "componente": componente,
                    }
                    
                    # Processar submissão
                    _process_estagio_submission(form_data, uploaded_files)
                    
                    st.success(
                        f"✅ **Documentos de estágio enviados com sucesso!**\n\n"
                        f"**Resumo:**\n"
                        f"- Nome: {nome}\n"
                        f"- Matrícula: {matricula}\n"
                        f"- Turma: {turma}\n"
                        f"- Componente: {componente}\n"
                        f"- Arquivo(s): {len(uploaded_files)} documento(s)\n\n"
                        f"Você receberá um e-mail de confirmação em breve.\n\n"
                        f"Redirecionando para a tela principal em 4 segundos..."
                    )
                    st.balloons()
                    
                    # Aguardar 4 segundos e redirecionar
                    time.sleep(4)
                    st.switch_page("main.py")
                    
                except Exception as e:
                    st.error(f"❌ **Erro ao processar envio:**\n\n{str(e)}")
                    st.info("Por favor, tente novamente ou entre em contato com o suporte.")


def main() -> None:
    st.set_page_config(
        page_title="Formulário Estágio - FasiTech",
        layout="centered",
        page_icon="📋",
        initial_sidebar_state="collapsed",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': None
        }
    )
    render_form()


main()
