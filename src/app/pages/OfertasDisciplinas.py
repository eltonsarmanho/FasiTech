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

# Cache para leitura de abas e dados das planilhas
@st.cache_data(show_spinner=False)
def cached_get_sheet_tabs(sheet_id):
    return get_sheet_tabs(sheet_id)

@st.cache_data(show_spinner=False)
def cached_read_sheet_tab(sheet_id, tab_name):
    return read_sheet_tab(sheet_id, tab_name)

# Cache para dados processados
@st.cache_data(show_spinner=False)
def process_oferta_data(sheet_id, tab_name):
    """Processa dados de oferta com cache para evitar reprocessamento."""
    df_oferta = cached_read_sheet_tab(sheet_id, tab_name)
    df_oferta.dropna(how='all', inplace=True)
    
    if df_oferta.empty or 'Turma' not in df_oferta.columns:
        return df_oferta, {}, []
    
    # Processar ícones de plano de ensino
    if 'Plano de Ensino' in df_oferta.columns:
        df_oferta = df_oferta.copy()
        df_oferta['Plano de Ensino'] = df_oferta['Plano de Ensino'].apply(
            lambda val: '✅' if str(val).strip().lower() in ['true', 'sim', 'confirmado', 'ok', '1', 'yes']
            else '❌' if str(val).strip().lower() in ['false', 'não', 'nao', 'pendente', '0', 'no']
            else str(val) if pd.notna(val) else ''
        )
    
    # Criar mapa de cores
    df_display = df_oferta.dropna(subset=['Turma'])
    unique_turmas = sorted(df_display['Turma'].unique())
    palette = [
        "#44928e", "#a066a5", "#9b7c4b", "#907a94", "#4f7452", "#a0a0a0", "#bbec82", "#d34d61",
    ]
    color_map = {turma: palette[i % len(palette)] for i, turma in enumerate(unique_turmas)}
    
    return df_display, color_map, unique_turmas

@st.cache_data(show_spinner=False)
def process_grade_data(sheet_id, tab_name):
    """Processa dados de grade com cache."""
    df_grade = cached_read_sheet_tab(sheet_id, tab_name)
    df_grade.dropna(how='all', inplace=True)
    
    # Filtra linhas que são cabeçalhos repetidos
    if 'Semestre' in df_grade.columns:
        df_grade = df_grade[df_grade['Semestre'] != 'Semestre']
    
    return df_grade

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
    Pinta a linha inteira da disciplina ofertada, usando a cor da turma que oferta.
    """
    disciplina = row.get('Disciplina')
    if pd.notna(disciplina) and disciplina in disciplina_turma_cor:
        color = disciplina_turma_cor[disciplina]
        return [f'background-color: {color}'] * len(row)
    return [''] * len(row)
    


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
    
    # Carregamento otimizado das abas (cache)
    tabs = cached_get_sheet_tabs(SHEET_ID)
    grade_tabs = [t for t in tabs if t[0].isdigit() or t.lower().startswith("grade")]
    oferta_tabs = [t for t in tabs if t.lower().startswith("ofertas")]

    # ===== SEÇÃO OFERTAS =====
    st.markdown('<div class="tab-title">Ofertas de Disciplinas</div>', unsafe_allow_html=True)
    
    if oferta_tabs:
        tab_oferta_selecionada = st.selectbox("Selecione o período de ofertas:", oferta_tabs, key="oferta_tab")
        
        # Carregamento otimizado dos dados de oferta
        df_oferta_display, color_map, unique_turmas = process_oferta_data(SHEET_ID, tab_oferta_selecionada)
        
        if not df_oferta_display.empty:
            with st.container():
                # Aplicar estilo com cache
                styled_oferta = df_oferta_display.style.apply(style_turma, color_map=color_map, axis=1)
                cols_to_center = [c for c in df_oferta_display.columns if c != 'Disciplina']
                styled_oferta = styled_oferta.set_properties(**{'text-align': 'center'}, subset=cols_to_center)
                st.dataframe(styled_oferta, width='stretch')
        else:
            st.info("Nenhuma oferta de disciplinas encontrada para este período.")
    else:
        st.info("Nenhuma aba de oferta de disciplinas foi encontrada.")
        df_oferta_display = pd.DataFrame()
        color_map = {}

    # ===== SEÇÃO GRADE CURRICULAR =====
    st.markdown('<div class="tab-title">Grade Curricular</div>', unsafe_allow_html=True)
    
    if grade_tabs:
        turma_selecionada = st.selectbox("Selecione a grade curricular:", grade_tabs, key="grade_tab")
        
        # Carregamento otimizado dos dados de grade
        df_grade = process_grade_data(SHEET_ID, turma_selecionada)
        
        if not df_grade.empty and 'Disciplina' in df_grade.columns and not df_oferta_display.empty:
            # Cruzamento otimizado: usar color_map já processado
            disciplina_turma_cor = {}
            for _, oferta in df_oferta_display.iterrows():
                disciplina = oferta.get('Disciplina')
                turma = oferta.get('Turma')
                if turma == turma_selecionada and pd.notna(disciplina):
                    disciplina_turma_cor[disciplina] = color_map.get(turma_selecionada, "#e0f2f1")
            
            # Aplicar estilo apenas se houver disciplinas para pintar
            if disciplina_turma_cor:
                styled_grade = df_grade.style.apply(
                    style_disciplina_turma,
                    disciplina_turma_cor=disciplina_turma_cor,
                    axis=1
                )
                st.dataframe(styled_grade, width='stretch')
            else:
                st.dataframe(df_grade, width='stretch')
                st.info("💡 Nenhuma disciplina desta grade está sendo ofertada pela turma selecionada.")
        else:
            st.dataframe(df_grade, width='stretch')
    else:
        st.info("Nenhuma aba de grade curricular foi encontrada.")

    

if __name__ == "__main__":
    main()
