from __future__ import annotations

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

# Lista de professores
PROFESSORES = [
    "Allan Barbosa Costa",
    "Elton Sarmanho Siqueira",
    "Carlos dos Santos Portela",
    "Fabricio de Souza Farias",
    "Ulisses Weyl da Cunha Costa",
    "Diovanni Moraes de Araujo",
    "Leonardo Nunes Gonçalves",
    "Keventon Rian Guimarães Gonçalves",
]

# Opções de semestre
SEMESTRES = [
    "2025.4",
    "2026.1",
    "2026.2",
    "2026.3",
    "2026.4",
]


def _load_plano_settings() -> dict[str, Any]:
    """Carrega configurações de Plano de Ensino do secrets.toml."""
    try:
        return {
            "drive_folder_id": st.secrets["plano"]["drive_folder_id"],
            "sheet_id": st.secrets["plano"]["sheet_id"],
            "notification_recipients": st.secrets["plano"].get("notification_recipients", []),
        }
    except (KeyError, FileNotFoundError) as e:
        st.error(
            f"⚠️ Configurações de Plano de Ensino não encontradas em secrets.toml.\n\n"
            f"Por favor, configure a seção [plano] com:\n"
            f"- drive_folder_id\n"
            f"- sheet_id\n"
            f"- notification_recipients"
        )
        raise ValueError("Configurações de Plano de Ensino ausentes") from e


def _render_intro() -> None:
    st.markdown(
        """
        <style>
            /* Estilos alinhados com identidade visual institucional */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            
            /* Ocultar sidebar completamente - aplicação imediata */
            [data-testid="stSidebar"] {
                display: none !important;
                visibility: hidden !important;
                width: 0 !important;
                min-width: 0 !important;
                max-width: 0 !important;
            }
            [data-testid="collapsedControl"] {
                display: none !important;
                visibility: hidden !important;
            }
            section[data-testid="stSidebar"] {
                display: none !important;
                visibility: hidden !important;
            }
            [data-testid="stSidebarNav"] {
                display: none !important;
                visibility: hidden !important;
            }
            
            .plano-hero {
                background: linear-gradient(135deg, #1a0d2e 0%, #2d1650 50%, #4a1d7a 100%);
                border-radius: 16px;
                padding: 36px;
                color: #ffffff;
                margin-bottom: 32px;
                box-shadow: 0 10px 30px rgba(26, 13, 46, 0.25);
                position: relative;
                overflow: hidden;
            }
            
            .plano-hero::before {
                content: '';
                position: absolute;
                top: -30%;
                right: -5%;
                width: 300px;
                height: 300px;
                background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
                border-radius: 50%;
            }
            
            .plano-hero h1 {
                font-size: 1.9rem;
                margin-bottom: 16px;
                font-weight: 700;
                text-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            
            .plano-hero p {
                font-size: 1.05rem;
                line-height: 1.6;
                margin-bottom: 8px;
                opacity: 0.95;
            }
            
            .plano-card {
                background: #ffffff;
                border-radius: 16px;
                padding: 36px;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
                border: 1px solid #e2e8f0;
                margin-bottom: 24px;
            }
            
            .plano-required {
                color: #ef4444;
                font-weight: 700;
            }
            
            .info-box {
                background: #fef3c7;
                border-left: 4px solid #f59e0b;
                padding: 16px;
                margin: 20px 0;
                border-radius: 8px;
            }
            
            .info-box p {
                color: #78350f;
                margin: 4px 0;
                font-size: 0.95rem;
            }
            
            .info-box ul {
                color: #78350f;
                margin: 8px 0;
                padding-left: 20px;
            }
            
            .info-box li {
                margin: 4px 0;
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
        <div class="plano-hero">
            <h1>📚 Formulário de Envio de Plano de Ensino</h1>
            <p><strong>Submissão de Planos de Ensino por Disciplina</strong></p>
            <p>Preencha os campos abaixo e envie os documentos de plano de ensino.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Info Box
    st.markdown(
        """
        <div class="info-box">
            <p><strong>⚠️ Instruções importantes:</strong></p>
            <ul>
                <li><strong>Insira no formato Documento ou PDF</strong></li>
                <li><strong>Coloque por semestre</strong></li>
                <li><strong>Nome dos arquivos deve seguir esse Padrão: [Docente] Plano de Ensino - Disciplina</strong></li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _validate_submission(
    docente: str,
    semestre: str,
    uploaded_files: list,
) -> list[str]:
    """Executa validações básicas antes de enviar ao backend."""
    errors: list[str] = []
    
    # Docente obrigatório
    if not docente or docente == "Outro:":
        errors.append("Nome do Docente Responsável é obrigatório.")
    
    # Semestre obrigatório
    if not semestre:
        errors.append("Semestre é obrigatório.")
    
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


def _process_plano_submission(form_data: dict[str, Any], files: list) -> None:
    """Processa submissão do formulário de plano de ensino."""
    from src.services import form_service
    
    # Processar submissão usando serviço centralizado
    form_service.process_plano_submission(form_data, files)


def render_form() -> None:
    _render_intro()
    
    
    # ============================================
    # SEÇÃO FORA DO FORM: Docente (com campo condicional "Outro:")
    # ============================================
    st.markdown("### 👨‍🏫 Nome do Docente Responsável")
    st.markdown("<span class='plano-required'>*</span> Selecione o docente antes de preencher o restante do formulário", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Radio buttons para seleção de docente
    docente = st.radio(
        "Nome do Docente Responsável *",
        options=PROFESSORES + ["Outro:"],
        key="docente_select",
        label_visibility="collapsed"
    )
    
    docente_outro = ""
    if docente == "Outro:":
        docente_outro = st.text_input(
            "Especifique o nome do docente *", 
            placeholder="Nome completo do docente",
            key="docente_outro_input"
        )
    
    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    
    # ============================================
    # FORMULÁRIO PRINCIPAL
    # ============================================
    with st.form("formulario_plano_ensino"):
        st.markdown("<span class='plano-required'>*</span> Todos os campos são obrigatórios", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Semestre
        st.markdown("### 📅 Semestre")
        semestre = st.selectbox(
            "Semestre *",
            options=[""] + SEMESTRES,
            format_func=lambda x: "Escolher" if x == "" else x,
            help="Selecione o semestre do plano de ensino"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Anexos
        st.markdown("### 📎 Anexos")
        st.markdown(
            f"<p style='color: #6b7280; font-size: 0.9rem;'>"
            f"Faça upload de até 10 arquivos aceitos: PDF ou document. O tamanho máximo é de 100 MB por item.</p>",
            unsafe_allow_html=True,
        )
        
        uploaded_files = st.file_uploader(
            "Adicionar arquivo",
            type=["pdf", "doc", "docx"],
            accept_multiple_files=True,
            help=f"Selecione um ou mais arquivos (máximo {MAX_FILE_SIZE_MB} MB cada)",
            label_visibility="collapsed"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Botão de envio
        submitted = st.form_submit_button("Enviar", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Processar submissão
    if submitted:
        # Determinar nome do docente final
        docente_final = docente_outro.strip() if docente == "Outro:" else docente
        
        errors = _validate_submission(
            docente_final, semestre, uploaded_files or []
        )
        
        if errors:
            st.error("**❌ Erros encontrados:**\n\n" + "\n".join(f"• {error}" for error in errors))
        else:
            with st.spinner("Processando envio de plano de ensino..."):
                try:
                    # Preparar dados do formulário
                    form_data = {
                        "docente": docente_final,
                        "semestre": semestre,
                    }
                    
                    # Processar submissão
                    _process_plano_submission(form_data, uploaded_files)
                    
                    st.success(
                        f"✅ **Plano de ensino enviado com sucesso!**\n\n"
                        f"**Resumo:**\n"
                        f"- Docente: {docente_final}\n"
                        f"- Semestre: {semestre}\n"
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
        page_title="Formulário Plano de Ensino - FasiTech",
        layout="centered",
        page_icon="📚",
        initial_sidebar_state="collapsed",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': None
        }
    )
    render_form()


main()
