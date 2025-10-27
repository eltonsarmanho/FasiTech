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

def style_periodo(row, color_map):
    periodo = row.get('Período')
    if pd.notna(periodo):
        # Acessar o mapa de cores com o valor float do período
        color = color_map.get(periodo, '')
        if color:
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
    st.markdown('<div class="tab-title">Grade Curricular</div>', unsafe_allow_html=True)
    if grade_tabs:
        tab_grade = st.selectbox("Selecione a grade curricular:", grade_tabs, key="grade_tab")
        df_grade = read_sheet_tab(SHEET_ID, tab_grade)
        df_grade.dropna(how='all', inplace=True)
        
        if not df_grade.empty and 'Período' in df_grade.columns:
            # Limpeza e conversão da coluna 'Período'
            df_grade.dropna(subset=['Período'], inplace=True)
            # Converte para numérico, tratando erros e floats, sem converter para int
            df_grade['Período'] = pd.to_numeric(df_grade['Período'], errors='coerce')
            df_grade.dropna(subset=['Período'], inplace=True)

            # Criar mapa de cores
            unique_periods = sorted(df_grade['Período'].unique())
            # Paleta de cores em tons de roxo, de claro a escuro
            palette = [
                '#f2e7fe', '#e5d0fb', '#d8b9f8', '#ca9ff5', '#bc85f1', 
                '#ae6cee', '#a152ea', '#9338e6', '#861ee2', '#7804de'
            ]
            
            color_map = {
                period: palette[i % len(palette)] 
                for i, period in enumerate(unique_periods)
            }

            styled_grade = df_grade.style.apply(style_periodo, color_map=color_map, axis=1).format({'Período': '{:.1f}'})
            st.dataframe(styled_grade, use_container_width=True)
        else:
            st.dataframe(df_grade, use_container_width=True)

    st.markdown('<div class="tab-title">Ofertas de Disciplinas</div>', unsafe_allow_html=True)
    if oferta_tabs:
        tab_oferta = st.selectbox("Selecione o período de ofertas:", oferta_tabs, key="oferta_tab")
        df_oferta = read_sheet_tab(SHEET_ID, tab_oferta)
        df_oferta.dropna(how='all', inplace=True)

        if not df_oferta.empty and 'Turma' in df_oferta.columns:
            df_oferta.dropna(subset=['Turma'], inplace=True)

            # Criar mapa de cores para Turma
            unique_turmas = sorted(df_oferta['Turma'].unique())
            # Paleta de cores diversas em tons claros (Verde, Azul, Laranja, etc.)
            palette = [
                "#44928e",  # Verde-água claro
                "#a066a5",  # Azul claro
                "#9b7c4b",  # Laranja claro
                "#907a94",  # Roxo claro
                "#4f7452",  # Verde claro
                "#a0a0a0",  # Amarelo claro
                "#bbec82",  # Lima claro
                "#d34d61",  # Vermelho/Rosa claro
            ]
            print(unique_turmas)
            color_map = {
                turma: palette[i % len(palette)]
                for i, turma in enumerate(unique_turmas)
            }
            print(color_map)

            styled_oferta = df_oferta.style.apply(style_turma, color_map=color_map, axis=1)
            st.dataframe(styled_oferta, use_container_width=True)
        else:
            st.dataframe(df_oferta, use_container_width=True)

if __name__ == "__main__":
    main()
