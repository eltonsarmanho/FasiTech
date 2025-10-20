from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Adicionar diretório raiz ao PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

LOGO_PATH = Path(__file__).resolve().parents[2] / "resources" / "fasiOficial.png"


def _render_intro() -> None:
    st.markdown(
        """
        <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            
            .form2-hero {
                background: linear-gradient(135deg, #1a0d2e 0%, #2d1650 50%, #4a1d7a 100%);
                border-radius: 16px;
                padding: 36px;
                color: #ffffff;
                margin-bottom: 32px;
                box-shadow: 0 10px 30px rgba(26, 13, 46, 0.25);
                text-align: center;
            }
            .form2-hero h1 {
                font-size: 1.9rem;
                margin-bottom: 12px;
                font-weight: 700;
            }
            .form2-card {
                background: #ffffff;
                border-radius: 16px;
                padding: 36px;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
                border: 1px solid #e2e8f0;
            }
            .logo-container {
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 16px;
                background: #ffffff;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
                margin-bottom: 16px;
            }
            .stButton > button {
                background: linear-gradient(135deg, #4a1d7a 0%, #7c3aed 100%);
                color: #ffffff;
                border: none;
                font-weight: 600;
                padding: 16px 32px;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(74, 29, 122, 0.25);
            }
            .stButton > button:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 24px rgba(74, 29, 122, 0.4);
                background: linear-gradient(135deg, #5a2d8a 0%, #8c4afd 100%);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Logo
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        if LOGO_PATH.exists():
            st.markdown('<div class="logo-container">', unsafe_allow_html=True)
            st.image(str(LOGO_PATH), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Hero
    st.markdown(
        """
        <div class="form2-hero">
            <h1>📄 Outros Formulários</h1>
            <p>Este formulário está em desenvolvimento e em breve estará disponível.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_form() -> None:
    _render_intro()
    st.markdown('<div class="form2-card">', unsafe_allow_html=True)
    
    st.info("🚧 **Em Desenvolvimento** - Este formulário ainda não está implementado.")
    
    st.markdown("### 🔜 Funcionalidades Planejadas")
    st.markdown("""
    - ✅ Solicitações acadêmicas diversas
    - ✅ Upload de documentos complementares
    - ✅ Acompanhamento de status em tempo real
    - ✅ Notificações automáticas por e-mail
    - ✅ Histórico de solicitações
    """)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("← Voltar para Página Inicial", use_container_width=True):
        st.switch_page("main.py")
    
    st.markdown('</div>', unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(
        page_title="Outros Formulários - FasiTech",
        layout="centered",
        page_icon="📄",
        initial_sidebar_state="collapsed"
    )
    render_form()


main()
