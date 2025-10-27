from __future__ import annotations
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
from typing import List, Dict

# Identidade visual
LOGO_PATH = Path(__file__).resolve().parents[2] / "resources" / "fasiOficial.png"

# Adicionar diretório raiz ao PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Carregar sheet_id do secrets
SHEET_ID = st.secrets["ofertas"]["sheet_id"]

# Função para buscar abas da planilha
from src.services.google_sheets import get_sheet_tabs, read_sheet_tab

def _render_custom_styles():
    st.markdown(
        """
        <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            [data-testid="stSidebar"],
            section[data-testid="stSidebar"],
            [data-testid="collapsedControl"],
            [data-testid="stSidebarNav"] {
                display: none !important;
                visibility: hidden !important;
                width: 0 !important;
                min-width: 0 !important;
                max-width: 0 !important;
            }
            .logo-container {
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
                background: #fff;
                border-radius: 16px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                margin-bottom: 20px;
            }
            .fasi-header {
                background: linear-gradient(135deg, #1a0d2e 0%, #2d1650 50%, #4a1d7a 100%);
                border-radius: 20px;
                padding: 32px;
                margin-bottom: 32px;
                color: #fff;
                box-shadow: 0 10px 40px rgba(26, 13, 46, 0.3);
                position: relative;
                overflow: hidden;
            }
            .fasi-header h1 {
                font-size: 2.1rem;
                font-weight: 700;
                margin-bottom: 10px;
                text-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            .fasi-header p {
                color: rgba(255,255,255,0.92);
                font-size: 1.08rem;
                line-height: 1.6;
                margin: 0;
            }
            .tab-title {
                color: #1a0d2e;
                font-size: 1.2rem;
                font-weight: 600;
                margin-top: 24px;
                margin-bottom: 8px;
                border-bottom: 2px solid #7c3aed;
                padding-bottom: 4px;
            }
            .stDataFrame {
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(74,29,122,0.08);
                margin-bottom: 32px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def style_disciplina_turma(row, disciplina_turma_cor):
    """
    Pinta apenas a célula da disciplina ofertada, usando a cor da turma que oferta.
    """
    styled = [''] * len(row)
    disciplina = row.get('Disciplina')
    if pd.notna(disciplina) and disciplina in disciplina_turma_cor:
        # Descobre o índice da coluna Disciplina
        col_names = list(row.index)
        idx = col_names.index('Disciplina')
        styled[idx] = f'background-color: {disciplina_turma_cor[disciplina]}'
    return styled


def style_turma(row, color_map):
    turma = row.get('Turma')
    if pd.notna(turma):
        color = color_map.get(turma, '')
        if color:
            return [f'background-color: {color}'] * len(row)
    return [''] * len(row)

def main():
    st.set_page_config(
        page_title="Ofertas de Disciplinas",
        layout="wide",
        page_icon="📅",
        initial_sidebar_state="collapsed",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': None
        }
    )
    _render_custom_styles()
    # Logo
    col_left, col_center, col_right = st.columns([1,2,1])
    with col_center:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width='stretch')
            st.markdown('</div>', unsafe_allow_html=True)
    # Header
    st.markdown(
        """
        <div class="fasi-header">
            <h1>📅 Ofertas de Disciplinas</h1>
            <p>Consulte as grades curriculares e ofertas de disciplinas por período e campus.<br>
            Visualize turmas, professores, carga horária e status do plano de ensino.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # Buscar abas
    tabs = get_sheet_tabs(SHEET_ID)
    # Separar abas de grade e de ofertas
    grade_tabs = [t for t in tabs if t[0].isdigit() or t.lower().startswith("grade")]
    oferta_tabs = [t for t in tabs if t.lower().startswith("ofertas")]

    # Carregar dados de oferta antes de tudo
    df_oferta = pd.DataFrame()
    
    st.markdown('<div class="tab-title">Ofertas de Disciplinas</div>', unsafe_allow_html=True)
    if oferta_tabs:
        tab_oferta_selecionada = st.selectbox("Selecione o período de ofertas:", oferta_tabs, key="oferta_tab")
        df_oferta = read_sheet_tab(SHEET_ID, tab_oferta_selecionada)
        df_oferta.dropna(how='all', inplace=True)
    if not df_oferta.empty:
        if 'Turma' in df_oferta.columns:
            df_oferta_display = df_oferta.dropna(subset=['Turma'])
            # Criar mapa de cores para Turma
            unique_turmas = sorted(df_oferta_display['Turma'].unique())
            palette = [
                "#44928e", "#a066a5", "#9b7c4b", "#907a94", "#4f7452", "#a0a0a0", "#bbec82", "#d34d61",
            ]
            color_map = {turma: palette[i % len(palette)] for i, turma in enumerate(unique_turmas)}
            # Exibe todas as ofertas, pintando por turma
            styled_oferta = df_oferta_display.style.apply(style_turma, color_map=color_map, axis=1)
            st.dataframe(styled_oferta, use_container_width=True)
        else:
            st.dataframe(df_oferta, use_container_width=True)
    else:
        st.info("Nenhuma aba de oferta de disciplinas foi encontrada ou selecionada.")

    # Remove filtro de turma. Sempre cruza todas as ofertas com a grade.

    st.markdown('<div class="tab-title">Grade Curricular</div>', unsafe_allow_html=True)
    if grade_tabs:
        turma_selecionada = st.selectbox("Selecione a grade curricular:", grade_tabs, key="grade_tab")
        df_grade = read_sheet_tab(SHEET_ID, turma_selecionada)
        df_grade.dropna(how='all', inplace=True)
        if not df_grade.empty and 'Disciplina' in df_grade.columns and not df_oferta.empty:
            # Cruzamento: mapeia disciplina ofertada -> cor da turma (todas as turmas)
            palette = [
                "#44928e", "#a066a5", "#9b7c4b", "#907a94", "#4f7452", "#a0a0a0", "#bbec82", "#d34d61",
            ]
            turmas = sorted(df_oferta['Turma'].dropna().unique())
            color_map = {turma: palette[i % len(palette)] for i, turma in enumerate(turmas)}
            disciplina_turma_cor = {}
            for _, oferta in df_oferta.iterrows():
                disciplina = oferta.get('Disciplina')
                turma = oferta.get('Turma')
                if turma == turma_selecionada and pd.notna(disciplina):
                    disciplina_turma_cor[disciplina] = color_map.get(turma_selecionada, "#e0f2f1")
            styled_grade = df_grade.style.apply(
                style_disciplina_turma,
                disciplina_turma_cor=disciplina_turma_cor,
                axis=1
            )
            st.dataframe(styled_grade, )
        else:
            st.dataframe(df_grade, )

    

if __name__ == "__main__":
    main()
