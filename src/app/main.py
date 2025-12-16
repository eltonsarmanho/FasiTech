from __future__ import annotations

import sys
import os
from pathlib import Path

import streamlit as st
from streamlit import runtime
from streamlit.web import cli as stcli

# Adicionar diretório raiz ao PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


from src.utils.env_loader import load_environment

# Carregar variáveis de ambiente
load_environment()

LOGO_PATH = Path(__file__).resolve().parent.parent / "resources" / "fasiOficial.png"


def _render_custom_styles() -> None:
    """Aplica CSS customizado alinhado à identidade visual institucional."""
    st.markdown(
        """
        <style>
            /* Ocultar menu padrão do Streamlit */
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
            
            /* Reset de espaçamentos e otimizações de performance */
            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
                max-width: 1200px;
            }
            
            /* Otimizações globais para transições fluidas */
            * {
                -webkit-backface-visibility: hidden;
                backface-visibility: hidden;
            }
            
            .stApp {
                transition: all 0.3s ease-out;
            }
            
            /* Prevenção de flash durante navegação */
            .stSpinner {
                opacity: 0;
                transition: opacity 0.2s ease;
            }
            
            /* Cabeçalho institucional */
            .institutional-header {
                background: linear-gradient(135deg, #1a0d2e 0%, #2d1650 50%, #4a1d7a 100%);
                border-radius: 20px;
                padding: 40px;
                margin-bottom: 40px;
                box-shadow: 0 10px 40px rgba(26, 13, 46, 0.3);
                position: relative;
                overflow: hidden;
            }
            
            .institutional-header::before {
                content: '';
                position: absolute;
                top: -50%;
                right: -10%;
                width: 400px;
                height: 400px;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
                border-radius: 50%;
            }
            
            .institutional-header h1 {
                color: #ffffff;
                font-size: 2.2rem;
                font-weight: 700;
                margin-bottom: 12px;
                text-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            
            .institutional-header p {
                color: rgba(255, 255, 255, 0.9);
                font-size: 1.05rem;
                line-height: 1.6;
                margin: 0;
            }
            
            /* Cards de formulários - Agora padronizados */
            .form-card-unified {
                border-radius: 16px;
                padding: 30px;
                margin-bottom: 24px;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
                transition: all 0.3s ease;
                text-align: center;
                color: white;
                cursor: pointer;
            }
            
            .form-card-unified:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
            }
            
            .form-card-icon {
                font-size: 3rem;
                margin-bottom: 16px;
                display: inline-block;
                animation: float 3s ease-in-out infinite;
            }
            
            @keyframes float {
                0%, 100% { transform: translateY(0px); }
                50% { transform: translateY(-8px); }
            }
            
            /* Botões otimizados com visibilidade garantida */
            .stButton > button {
                width: 100%;
                background: linear-gradient(135deg, rgba(255,255,255,0.25) 0%, rgba(255,255,255,0.15) 100%) !important;
                color: #ffffff !important;
                border: 2px solid rgba(255,255,255,0.4) !important;
                font-weight: 600;
                padding: 14px 28px;
                border-radius: 25px;
                transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
                font-size: 0.95rem;
                text-transform: none;
                letter-spacing: 0.3px;
                backdrop-filter: blur(15px);
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255,255,255,0.3);
                margin-top: -10px;
                position: relative;
                z-index: 10;
                text-shadow: 0 1px 2px rgba(0,0,0,0.3);
            }
            
            .stButton > button:hover {
                background: linear-gradient(135deg, rgba(255,255,255,0.35) 0%, rgba(255,255,255,0.25) 100%) !important;
                border-color: rgba(255,255,255,0.6) !important;
                transform: translateY(-1px);
                box-shadow: 0 6px 24px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255,255,255,0.4);
                text-shadow: 0 1px 3px rgba(0,0,0,0.4);
            }
            
            .stButton > button:active {
                transform: translateY(0px);
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
            }
            
            .stButton > button:active {
                transform: translateY(0);
                transition: all 0.1s ease;
            }
            
            /* Base dos botões - design unificado */
            .stButton > button {
                width: 100% !important;
                color: #ffffff !important;
                font-weight: 600;
                padding: 14px 28px;
                border-radius: 25px;
                transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
                font-size: 0.95rem;
                text-transform: none;
                letter-spacing: 0.3px;
                backdrop-filter: blur(15px);
                margin-top: -10px;
                position: relative;
                z-index: 10;
                text-shadow: 0 1px 2px rgba(0,0,0,0.3);
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255,255,255,0.3);
                min-height: 48px;
            }
            
            /* TODOS OS BOTÕES - Cor Padrão Azul/Roxo (Discentes) */
            .stButton > button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                border: 2px solid rgba(102, 126, 234, 0.6) !important;
            }
            
            .stButton > button:hover {
                background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%) !important;
                border-color: rgba(102, 126, 234, 0.8) !important;
                transform: translateY(-1px);
                box-shadow: 0 6px 24px rgba(102, 126, 234, 0.4), inset 0 1px 0 rgba(255,255,255,0.4);
            }
            
            /* Estado ativo universal */
            .stButton > button:active {
                transform: translateY(0px);
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
                transition: all 0.1s ease;
            }
            
            /* CSS simplificado - todos os botões usam a mesma cor padrão */
            
            /* Animação float para ícones */
            @keyframes float {
                0%, 100% { transform: translateY(0px); }
                50% { transform: translateY(-8px); }
            }
            
            /* Container dos cards com hover */
            .form-card-container:hover {
                transform: translateY(-3px);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
            }
            
            /* Seção de informações */
            .info-section {
                background: linear-gradient(135deg, #f8fafc 0%, #e8eaf0 100%);
                border-radius: 16px;
                padding: 32px;
                margin-top: 48px;
                border-left: 6px solid #7c3aed;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
            }
            
            .info-section h4 {
                color: #1a0d2e;
                margin-bottom: 16px;
                font-size: 1.2rem;
                font-weight: 600;
            }
            
            .info-section ul {
                list-style: none;
                padding: 0;
                margin: 0;
            }
            
            .info-section li {
                color: #475569;
                line-height: 1.8;
                padding-left: 28px;
                position: relative;
                margin-bottom: 8px;
            }
            
            .info-section li::before {
                content: '✓';
                position: absolute;
                left: 0;
                color: #7c3aed;
                font-weight: bold;
                font-size: 1.2rem;
            }
            
            /* Títulos de seção */
            .section-title {
                color: #1a0d2e;
                font-size: 1.8rem;
                font-weight: 700;
                margin-bottom: 24px;
                padding-bottom: 12px;
                border-bottom: 3px solid #7c3aed;
                display: inline-block;
            }
            
            /* Logo container */
            .logo-container {
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
                background: #ffffff;
                border-radius: 16px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
                margin-bottom: 20px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_header() -> None:
    """Renderiza o cabeçalho com logo e título institucional."""
    # Logo centralizado
    col_left, col_center, col_right = st.columns([1, 2, 1])
    
    with col_center:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width='stretch')
    
    # Hero section
    st.markdown(
        """
        <div class="institutional-header">
            <h1>🎓 Portal de Formulários Acadêmicos</h1>
            <p>Bem-vindo ao sistema de formulários da FASI.</p>
            <p>Selecione o formulário desejado abaixo e preencha com atenção todas as informações solicitadas.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_form_card(
    title: str, 
    description: str, 
    icon: str, 
    page_name: str,
    key: str,
    gradient_colors: str = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
) -> None:
    """Renderiza um card de formulário com navegação fluida via Streamlit button."""
    button_text_map = {
        "Ofertas de Disciplinas": "Ofertas",
        "Formulário de ACC": "Formulário",
        "Formulário TCC": "Formulário",
        "Formulário de Estágio": "Formulário",
        "Requerimento de TCC": "Requerimento",
        "Formulário Social": "Formulário",
        "FAQ - Perguntas Frequentes": "FAQ",
        "Plano de Ensino": "Planos",
        "Projetos": "Projetos"
    }
    button_text = button_text_map.get(title, title)
    
    # Container com estilo customizado
    st.markdown(
        f"""
        <div class="form-card-container" style="
            background: {gradient_colors};
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 24px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            text-align: center;
            color: white;
            position: relative;
            overflow: hidden;
        ">
            <div style="font-size: 3rem; margin-bottom: 16px; animation: float 3s ease-in-out infinite;">{icon}</div>
            <h3 style="color: white; font-size: 1.5rem; margin-bottom: 12px; font-weight: 600;width: 102%;">
                {title}
            </h3>
            <p style="color: rgba(255,255,255,0.9); font-size: 0.95rem; line-height: 1.7; margin-bottom: 20px;">
                {description}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Botão Streamlit nativo com classe específica para cores correspondentes
    if st.button(
        f"📋 Acessar {button_text}",
        key=key,
        use_container_width=True,
        type="secondary"
    ):
        st.switch_page(f"pages/{page_name}")


def _render_available_forms() -> None:
    """Renderiza as três seções de formulários organizadas por público-alvo."""
    # Obter URL da API das variáveis de ambiente
    api_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
    
    # SEÇÃO 1: FORMULÁRIOS PARA DISCENTES
    st.markdown('<h2 class="section-title">🎓 Formulários Disponíveis para Discentes</h2>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Primeira linha: FormACC | FormTCC | FormEstagio
    col1, col2, col3 = st.columns(3, gap="large")
    with col1:
        _render_form_card(
            title="Formulário de ACC",
            description="Submissão de Atividades Complementares Curriculares. Envie seus certificados consolidados em um único arquivo PDF para análise e validação.",
            icon="🎓",
            page_name="FormACC.py",
            key="btn_acc",
            gradient_colors="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"  # Azul/Roxo - Discentes
        )
    with col2:
        _render_form_card(
            title="Formulário TCC",
            description="Submissão de Trabalho de Conclusão de Curso (TCC 1 e TCC 2). Envie os documentos obrigatórios conforme as diretrizes do seu componente curricular.",
            icon="📚",
            page_name="FormTCC.py",
            key="btn_tcc",
            gradient_colors="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"  # Azul/Roxo - Discentes
        )
    with col3:
        _render_form_card(
            title="Formulário de Estágio",
            description="Envio de documentos de Estágio I e Estágio II. Submeta o Plano de Estágio ou Relatório Final conforme o componente curricular.",
            icon="📋",
            page_name="FormEstagio.py",
            key="btn_estagio",
            gradient_colors="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"  # Azul/Roxo - Discentes
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Segunda linha: Requerimento TCC | Formulário Social
    col4, col5, col6 = st.columns(3, gap="large")
    with col4:
        _render_form_card(
            title="Requerimento de TCC",
            description="Registro de informações para defesa do TCC. Cadastre os dados da banca examinadora e informações adicionais sobre seu TCC.",
            icon="📝",
            page_name="FormRequerimentoTCC.py",
            key="btn_requerimento",
            gradient_colors="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"  # Azul/Roxo - Discentes
        )
    with col5:
        _render_form_card(
            title="Formulário Social",
            description="Questionário de perfil social, acadêmico, inclusão, diversidade e saúde mental. Dados para políticas institucionais e estudantil.",
            icon="🤝",
            page_name="FormSocial.py",
            key="btn_social",
            gradient_colors="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"  # Azul/Roxo - Discentes
        )
    with col6:
        _render_form_card(
            title="Avaliação da Gestão",
            description="Avalie a gestão da Faculdade de Sistemas de Informação. Feedback anônimo sobre transparência, comunicação e suporte.",
            icon="📊",
            page_name="FormAutoAvaliacaoFASI.py",
            key="btn_avaliacao_gestao",
            gradient_colors="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"  # Cor Padrão
        )

    st.markdown("<br><br>", unsafe_allow_html=True)

    # SEÇÃO 2: FORMULÁRIOS PARA DOCENTES
    st.markdown('<h2 class="section-title">👨‍🏫 Formulários Disponíveis para Docentes</h2>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col7, col8, col9 = st.columns(3, gap="large")
    with col7:
        _render_form_card(
            title="Plano de Ensino",
            description="Submissão de Planos de Ensino por disciplina. Docentes podem enviar os planos de ensino organizados por semestre.",
            icon="📖",
            page_name="FormPlanoEnsino.py",
            key="btn_plano",
            gradient_colors="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"  # Cor Padrão
        )
    with col8:
        _render_form_card(
            title="Projetos",
            description="Submissão de Projetos de Ensino, Pesquisa e Extensão. Docentes podem registrar novos projetos, renovações ou encerramentos.",
            icon="🔬",
            page_name="FormProjetos.py",
            key="btn_projetos",
            gradient_colors="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"  # Cor Padrão
        )

    st.markdown("<br><br>", unsafe_allow_html=True)

    # SEÇÃO 3: GERAL
    st.markdown('<h2 class="section-title">🌐 Geral</h2>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col10, col11, col12 = st.columns(3, gap="large")
    with col10:
        _render_form_card(
            title="Diretor Virtual",
            description="Assistente inteligente para orientar sobre informações sobre matrículas, estágio e outros assuntos acadêmicos.",
            icon="🤖",
            page_name="PageDiretorVirtual.py",
            key="btn_diretor_virtual",
            gradient_colors="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"  # Cor Padrão
        )
    with col11:
        _render_form_card(
            title="FAQ",
            description="Encontre respostas para as dúvidas mais comuns sobre matrículas, estágio e outros assuntos.",
            icon="❓",
            page_name="FAQ.py",
            key="btn_faq",
            gradient_colors="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"  # Cor Padrão
        )
    with col12:
        # Card especial para download de dados sociais - seguindo padrão dos demais
        download_url = f"{api_url}/api/v1/dados-sociais/download"
        
        # Container com estilo customizado (mesmo padrão)
        st.markdown(
            """
            <div class="form-card-container" style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 16px;
                padding: 30px;
                margin-bottom: 24px;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                text-align: center;
                color: white;
                position: relative;
                overflow: hidden;
            ">
                <div style="font-size: 3rem; margin-bottom: 16px; animation: float 3s ease-in-out infinite;">📊</div>
                <h3 style="color: white; font-size: 1.5rem; margin-bottom: 12px; font-weight: 600;">
                    Dados Sociais
                </h3>
                <p style="color: rgba(255,255,255,0.9); font-size: 0.95rem; line-height: 1.7; margin-bottom: 20px;">
                    Download dos dados sociais dos discentes para pesquisa. Dados anonimizados conforme LGPD.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # Botão Streamlit nativo (mesmo padrão dos demais)
        if st.button(
            "📥 Baixar Dados",
            key="btn_dados_sociais",
            use_container_width=True,
            type="secondary"
        ):
            st.markdown(f'<meta http-equiv="refresh" content="0; url={download_url}">', unsafe_allow_html=True)
            st.success("🔄 Redirecionando para download...")
    #     _render_form_card(
    #         title="Ofertas de Disciplinas",  
    #         description="Consulta das ofertas de disciplinas do semestre e grades curriculares. Visualização por período e turma.",
    #         icon="📅",
    #         page_name="OfertasDisciplinas.py",
    #         key="btn_ofertas",
    #         gradient_colors="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"  # Cor Padrão
    #     )

    st.markdown("<br>", unsafe_allow_html=True)

        


def _render_info_section() -> None:
    """Renderiza seção informativa com orientações importantes."""
    st.markdown(
        """
        <div class="info-section">
            <h4>ℹ️ Informações Importantes</h4>
            <ul>
                <li>Todos os formulários exigem dados pessoais e documentos em formato PDF ou DOC</li>
                <li>Certifique-se de que sua matrícula está ativa no SIGAA antes de enviar qualquer solicitação</li>
                <li>Você receberá confirmação por e-mail após o processamento da sua solicitação</li>
                <li>Os documentos são armazenados de forma segura no Google Drive institucional</li>
                <li>Em caso de dúvidas, entre em contato com a secretaria acadêmica (fasicuntins@ufpa.br)</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Página principal do portal de formulários."""
    st.set_page_config(
        page_title="FasiTech Forms Portal",
        layout="wide",
        page_icon="🎓",
        initial_sidebar_state="collapsed",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': None
        }
    )
    
    # Aplicar estilos primeiro para evitar flash
    _render_custom_styles()
    
    # Renderizar conteúdo principal
    _render_header()
    _render_available_forms()
    _render_info_section()
    
    # Rodapé com autor e LinkedIn
    st.markdown(
        '''<div style="text-align:center; margin-top:40px; color:#888; font-size:0.95rem;">
            Sistema desenvolvido por <strong>Elton Sarmanho</strong>
            <a href="https://www.linkedin.com/in/elton-sarmanho-836553185/" target="_blank" style="margin-left:8px; text-decoration:none; vertical-align:middle;">
                <img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/linkedin.svg" alt="LinkedIn" style="width:20px; height:20px; display:inline; vertical-align:middle; filter: grayscale(1) brightness(0.5); margin-bottom:2px;"> 
            </a>
        </div>''',
        unsafe_allow_html=True
    )


if __name__ == '__main__':
    if runtime.exists():
        main()
    else:
        sys.argv = ["streamlit", "run",  "--client.showSidebarNavigation=False",sys.argv[0]]
        sys.exit(stcli.main())
