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
# Aumentado para 50MB para acomodar apresentações PowerPoint grandes
MAX_FILE_SIZE_MB = 50

# Lista de professores/docentes
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

# Opções de carga horária
CARGAS_HORARIAS = ["0", "10", "20"]

# Opções de edital
EDITAIS = [
    "Eixo Transversal",
    "Navega Saberes",
    "PIBEX",
    "PIBIC",
    "LabInfra",
    "Monitoria",
    "Executado sem Fomento",
]

# Opções de natureza
NATUREZAS = ["Ensino", "Extensão", "Pesquisa"]

# Opções de solicitação
SOLICITACOES = ["Novo", "Encerramento", "Renovação"]


def _load_projetos_settings() -> dict[str, Any]:
    """Carrega configurações de Projetos do secrets.toml."""
    try:
        return {
            "drive_folder_id": st.secrets["projetos"]["drive_folder_id"],
            "sheet_id": st.secrets["projetos"]["sheet_id"],
            "notification_recipients": st.secrets["projetos"].get("notification_recipients", []),
            "pareceristas": st.secrets["projetos"].get("pareceristas", ""),
        }
    except (KeyError, FileNotFoundError) as e:
        st.error(
            f"⚠️ Configurações de Projetos não encontradas em secrets.toml.\n\n"
            f"Por favor, configure a seção [projetos] com:\n"
            f"- drive_folder_id\n"
            f"- sheet_id\n"
            f"- notification_recipients\n"
            f"- pareceristas"
        )
        raise ValueError("Configurações de Projetos ausentes") from e


def _parse_pareceristas(pareceristas_str: str) -> dict[str, str]:
    """
    Converte string de pareceristas em dicionário.
    Formato: "Nome1:email1,Nome2:email2,..."
    """
    pareceristas_dict = {}
    if pareceristas_str:
        pares = pareceristas_str.split(",")
        for par in pares:
            if ":" in par:
                nome, email = par.split(":", 1)
                pareceristas_dict[nome.strip()] = email.strip()
    return pareceristas_dict


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
            
            .projetos-hero {
                background: linear-gradient(135deg, #1a0d2e 0%, #2d1650 50%, #4a1d7a 100%);
                border-radius: 16px;
                padding: 36px;
                color: #ffffff;
                margin-bottom: 32px;
                box-shadow: 0 10px 30px rgba(26, 13, 46, 0.25);
                position: relative;
                overflow: hidden;
            }
            
            .projetos-hero::before {
                content: '';
                position: absolute;
                top: -30%;
                right: -5%;
                width: 300px;
                height: 300px;
                background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
                border-radius: 50%;
            }
            
            .projetos-hero h1 {
                font-size: 1.9rem;
                margin-bottom: 16px;
                font-weight: 700;
                text-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            
            .projetos-hero p {
                font-size: 1.05rem;
                line-height: 1.6;
                margin-bottom: 8px;
                opacity: 0.95;
            }
            
            .projetos-required {
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
            st.image(str(LOGO_PATH), width='stretch')
    
    # Hero Section
    st.markdown(
        """
        <div class="projetos-hero">
            <h1>🔬 Formulário de Submissão de Projetos</h1>
            <p><strong>Registro e Acompanhamento de Projetos de Ensino, Pesquisa e Extensão</strong></p>
            <p>Preencha os campos abaixo para registrar novo projeto, solicitar renovação ou encerramento.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_solicitacao_info(solicitacao: str) -> None:
    """Renderiza informações específicas baseadas no tipo de solicitação."""
    if solicitacao == "Novo":
        st.markdown(
            """
            <div class="info-box">
                <p><strong>ℹ️ Documentos obrigatórios para NOVO projeto:</strong></p>
                <ul>
                    <li><strong>I - Requerimento do projeto</strong> (Obrigatório independente da Solicitação)</li>
                    <li><strong>II - O documento completo do projeto</strong></li>
                    <li><strong>III - Artefatos relevantes que apoiam o trabalho</strong> (Se houver)</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif solicitacao == "Encerramento":
        st.markdown(
            """
            <div class="info-box">
                <p><strong>ℹ️ Documentos obrigatórios para ENCERRAMENTO:</strong></p>
                <ul>
                    <li><strong>I - Requerimento</strong> Solicitando Encerramento e Renovação do projeto (anexar artefatos do projeto para prestação de contas e para validação do ano atual). Coloque nome dos artefatos com final <strong>'finalização'</strong> para facilitar identificação.</li>
                    <li><strong>IV - Relatório final</strong> (Caso for de renovação ou encerramento)</li>
                </ul>
                <p><strong>Obs:</strong> Número máximo de arquivos para não ultrapassar a cota de 10</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif solicitacao == "Renovação":
        st.markdown(
            """
            <div class="info-box">
                <p><strong>ℹ️ Documentos obrigatórios para RENOVAÇÃO:</strong></p>
                <ul>
                    <li><strong>I - Requerimento</strong> Solicitando Encerramento e Renovação do projeto (anexar artefatos do projeto para prestação de contas e para validação do ano atual). Coloque nome dos artefatos com final <strong>'finalização'</strong> para ajudar na identificação do artefatos relacionados a finalização do projeto</li>
                    <li><strong>IV - Relatório final</strong> (Caso for de renovação ou encerramento)</li>
                    <li><strong>V - Para casos de RENOVAÇÃO</strong> do projeto, então você deve enviar <strong>Requerimento</strong> (anexar artefatos do projeto com <strong>'finalização'</strong> para ajudar na identificação) do artefatos relacionados a finalização do projeto</li>
                </ul>
                <p><strong>Obs:</strong> Número máximo de arquivos para não ultrapassar a cota de 10</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _validate_submission(
    docente: str,
    parecerista1: str,
    parecerista2: str,
    nome_projeto: str,
    carga_horaria: str,
    edital: str,
    edital_outro: str,
    natureza: str,
    ano_edital: str,
    solicitacao: str,
    uploaded_files: list,
) -> list[str]:
    """Executa validações básicas antes de enviar ao backend."""
    errors: list[str] = []
    
    # Docente obrigatório
    if not docente:
        errors.append("Nome do Docente Responsável é obrigatório.")
    
    # Pareceristas obrigatórios
    if not parecerista1:
        errors.append("Nome do Parecerista 1 é obrigatório.")
    
    if not parecerista2:
        errors.append("Nome do Parecerista 2 é obrigatório.")
    
    # Pareceristas não podem ser iguais
    if parecerista1 and parecerista2 and parecerista1 == parecerista2:
        errors.append("Parecerista 1 e Parecerista 2 devem ser diferentes.")
    
    # Nome do projeto obrigatório
    if not nome_projeto.strip():
        errors.append("Nome do Projeto é obrigatório.")
    
    # Carga horária obrigatória
    if not carga_horaria:
        errors.append("Carga Horária é obrigatória.")
    
    # Edital obrigatório - validar se escolheu "Outro:" e não preencheu o campo
    if edital == "Outro:" and not edital_outro.strip():
        errors.append("Você selecionou 'Outro:', por favor especifique o nome do edital.")
    elif not edital:
        errors.append("Edital é obrigatório.")
    
    # Natureza obrigatória
    if not natureza:
        errors.append("Natureza é obrigatória.")
    
    # Ano do edital obrigatório
    if not ano_edital.strip():
        errors.append("Ano do Edital é obrigatório.")
    
    # Solicitação obrigatória
    if not solicitacao:
        errors.append("Solicitação é obrigatória.")
    
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


def _process_projetos_submission(form_data: dict[str, Any], files: list) -> None:
    """Processa submissão do formulário de projetos."""
    from src.services import form_service
    
    # Processar submissão usando serviço centralizado
    form_service.process_projetos_submission(form_data, files)


def render_form() -> None:
    _render_intro()
    
    # ============================================
    # SOLICITAÇÃO
    # ============================================
    st.markdown("### 📋 Solicitação")
    st.markdown("<span class='projetos-required'>*</span> Campo obrigatório", unsafe_allow_html=True)
    
    solicitacao = st.radio(
        "Solicitação *",
        options=SOLICITACOES,
        key="solicitacao_select",
        label_visibility="collapsed"
    )
    
    # Renderizar info box baseado na solicitação
    _render_solicitacao_info(solicitacao)
    
    # ============================================
    # DOCENTE RESPONSÁVEL
    # ============================================
    st.markdown("### 👨‍🏫 Nome do Docente Responsável")
    docente = st.radio(
        "Nome do Docente Responsável *",
        options=PROFESSORES,
        key="docente_select",
        label_visibility="collapsed"
    )
    
    # ============================================
    # PARECERISTAS
    # ============================================
    st.markdown("### 📝 Pareceristas")
    parecerista1 = st.radio(
        "Nome do Parecerista 1 *",
        options=PROFESSORES,
        key="parecerista1"
    )
    
    parecerista2 = st.radio(
        "Nome do Parecerista 2 *",
        options=PROFESSORES,
        key="parecerista2"
    )
    
    # ============================================
    # INFORMAÇÕES DO PROJETO
    # ============================================
    st.markdown("### 📊 Informações do Projeto")
    
    nome_projeto = st.text_input(
        "Nome do Projeto *",
        placeholder="Sua resposta",
        help="Digite o nome completo do projeto"
    )
    
    # Carga Horária
    st.markdown("**Carga Horária** <span class='projetos-required'>*</span>", unsafe_allow_html=True)
    carga_horaria = st.radio(
        "Carga Horária *",
        options=CARGAS_HORARIAS,
        horizontal=True,
        label_visibility="collapsed"
    )
    
    # Edital
    st.markdown("**Edital** <span class='projetos-required'>*</span>", unsafe_allow_html=True)
    edital = st.radio(
        "Edital *",
        options=EDITAIS + ["Outro:"],
        key="edital_select",
        label_visibility="collapsed"
    )
    
    # Campo condicional para "Outro:"
    edital_outro = ""
    if edital == "Outro:":
        edital_outro = st.text_input(
            "Especifique o nome do edital *",
            placeholder="Digite o nome do edital",
            key="edital_outro_input",
            help="Informe o nome do edital que não está na lista"
        )
    
    # Natureza
    st.markdown("**Natureza** <span class='projetos-required'>*</span>", unsafe_allow_html=True)
    natureza = st.radio(
        "Natureza *",
        options=NATUREZAS,
        horizontal=True,
        label_visibility="collapsed"
    )
    
    # Ano do Edital
    ano_edital = st.text_input(
        "Ano do Edital *",
        placeholder="2025",
        max_chars=4,
        help="Ano com 4 dígitos (ex: 2025)"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ============================================
    # FORMULÁRIO - APENAS ANEXOS E BOTÃO ENVIAR
    # ============================================
    with st.form("formulario_projetos"):
        # Anexos
        st.markdown("### 📎 Anexos")
        st.markdown(
            f"<p style='color: #6b7280; font-size: 0.9rem;'>"
            f"Faça upload de até 10 arquivos aceitos. O tamanho máximo é de {MAX_FILE_SIZE_MB} MB por item.</p>",
            unsafe_allow_html=True,
        )
        
        uploaded_files = st.file_uploader(
            "Adicionar arquivo",
            accept_multiple_files=True,
            help=f"Selecione um ou mais arquivos (máximo {MAX_FILE_SIZE_MB} MB cada)",
            label_visibility="collapsed"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Botão de envio
        
        col1, col2 = st.columns([1, 1])
        with col1:
            submitted = st.form_submit_button("Enviar", width='stretch')

        with col2:
            if st.form_submit_button("🏠 Voltar ao Menu Principal", width='stretch'):
                st.switch_page("main.py")
        # Processar submissão
        if submitted:
            # Inicializar flag se não existir
            if "projetos_processing" not in st.session_state:
                st.session_state.projetos_processing = False
            
            # Processar apenas se não estiver processando (previne múltiplos cliques)
            if not st.session_state.projetos_processing:
                # Marcar como processando
                st.session_state.projetos_processing = True
                
                # Determinar edital final
                edital_final = edital_outro.strip() if edital == "Outro:" else edital
                
                errors = _validate_submission(
                    docente, parecerista1, parecerista2, nome_projeto, carga_horaria,
                    edital, edital_outro, natureza, ano_edital, solicitacao, uploaded_files or []
                )
                
                if errors:
                    st.error("**❌ Erros encontrados:**\n\n" + "\n".join(f"• {error}" for error in errors))
                    st.session_state.projetos_processing = False  # Resetar
                else:
                    status_placeholder = st.empty()
                    status_placeholder.info("⏳ Processando dados da submissão. Aguarde...")
                    with st.spinner("Processando submissão de projeto... Gerando PDFs e enviando documentos..."):
                        try:
                            # Preparar dados do formulário
                            form_data = {
                                "docente": docente,
                                "parecerista1": parecerista1,
                                "parecerista2": parecerista2,
                                "nome_projeto": nome_projeto.strip(),
                                "carga_horaria": carga_horaria,
                                "edital": edital_final,
                                "natureza": natureza,
                                "ano_edital": ano_edital.strip(),
                                "solicitacao": solicitacao,
                            }
                            
                            # Processar submissão
                            _process_projetos_submission(form_data, uploaded_files)
                            
                            # Mensagem de PDFs gerados varia conforme tipo de solicitação
                            pdfs_gerados = "Parecer" if solicitacao == "Encerramento" else "Parecer e Declaração"
                            
                            st.success(
                                f"✅ **Projeto submetido com sucesso!**\n\n"
                                f"**Resumo:**\n"
                                f"- Docente: {docente}\n"
                                f"- Projeto: {nome_projeto}\n"
                                f"- Edital: {edital_final}\n"
                                f"- Natureza: {natureza}\n"
                                f"- Solicitação: {solicitacao}\n"
                                f"- Arquivo(s): {len(uploaded_files)} documento(s)\n"
                                f"- PDFs gerados: {pdfs_gerados}\n\n"
                                f"Você receberá um e-mail de confirmação com os documentos gerados."
                            )
                            status_placeholder.success("✅ Processamento concluído com sucesso.")
                            st.info("🏠 Processo finalizado. Retornando ao menu principal...")
                            
                            # Resetar flag
                            st.session_state.projetos_processing = False
                            
                            # Aguardar antes de redirecionar
                            time.sleep(st.secrets["sistema"]["timer"])
                            st.switch_page("main.py")
                            
                        except Exception as e:
                            status_placeholder.empty()
                            st.error(f"❌ **Erro ao processar submissão:**\n\n{str(e)}")
                            st.info("Por favor, tente novamente ou entre em contato com o suporte.")
                            # Resetar flag
                            st.session_state.projetos_processing = False


def main() -> None:
    st.set_page_config(
        page_title="Formulário Projetos - FasiTech",
        layout="centered",
        page_icon="🔬",
        initial_sidebar_state="collapsed",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': None
        }
    )
    render_form()


main()
