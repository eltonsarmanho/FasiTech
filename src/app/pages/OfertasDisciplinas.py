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

# Cache otimizado para leitura de abas e dados das planilhas
# TTL reduzido para 1800s (30min) com show_spinner para feedback visual
@st.cache_data(ttl=1800, show_spinner="🔄 Carregando abas da planilha...")
def cached_get_sheet_tabs(sheet_id):
    return get_sheet_tabs(sheet_id)

@st.cache_data(ttl=1800, show_spinner="📊 Carregando dados da planilha...")
def cached_read_sheet_tab(sheet_id, tab_name):
    return read_sheet_tab(sheet_id, tab_name)

# Cache otimizado para dados processados
@st.cache_data(ttl=1800, show_spinner="⚡ Processando dados de ofertas...")
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
    
    # Criar mapa de cores otimizado
    df_display = df_oferta.dropna(subset=['Turma'])
    unique_turmas = sorted(df_display['Turma'].unique())
    # Paleta de cores melhorada para melhor contraste
    palette = [
        "#2E86AB", "#A23B72", "#F18F01", "#C73E1D", "#6A994E", "#7209B7", 
        "#F77F00", "#D62828", "#003566", "#8B5CF6", "#10B981", "#F59E0B"
    ]
    color_map = {turma: palette[i % len(palette)] for i, turma in enumerate(unique_turmas)}
    
    return df_display, color_map, unique_turmas

@st.cache_data(ttl=1800, show_spinner="📋 Processando grade curricular...")
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
            
            /* Estilos para tabs */
            .stTabs > div > div > div > div {
                gap: 8px;
            }
            
            .stTabs [data-baseweb="tab-list"] {
                gap: 8px;
                background: #f8fafc;
                padding: 8px;
                border-radius: 12px;
            }
            
            .stTabs [data-baseweb="tab"] {
                background: #ffffff;
                border-radius: 8px;
                padding: 12px 20px;
                border: 1px solid #e2e8f0;
                transition: all 0.2s ease;
            }
            
            .stTabs [data-baseweb="tab"]:hover {
                background: #f1f5f9;
                border-color: #7c3aed;
            }
            
            .stTabs [aria-selected="true"] {
                background: linear-gradient(135deg, #7c3aed, #a855f7) !important;
                color: white !important;
                border-color: #7c3aed !important;
            }
            
            /* Métricas melhoradas */
            .metric-card {
                background: #f8fafc;
                border-radius: 12px;
                padding: 16px;
                border-left: 4px solid #7c3aed;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            
            /* Filtros */
            .stMultiSelect > div > div {
                border-radius: 8px;
                border: 2px solid #e2e8f0;
            }
            
            .stMultiSelect > div > div:focus-within {
                border-color: #7c3aed;
                box-shadow: 0 0 0 3px rgba(124,58,237,0.1);
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
    
    # Botão de atualização de dados
    col_refresh, col_empty = st.columns([1, 4])
   
    
    # Carregamento otimizado das abas (cache)
    tabs = cached_get_sheet_tabs(SHEET_ID)
    grade_tabs = [t for t in tabs if t[0].isdigit() or t.lower().startswith("grade")]
    oferta_tabs = [t for t in tabs if t.lower().startswith("ofertas")]

    # ===== INTERFACE COM TABS OTIMIZADAS =====
    if not oferta_tabs and not grade_tabs:
        st.error("❌ Nenhuma aba encontrada na planilha. Verifique a configuração.")
        return
    
    # Criar tabs principais
    tab_labels = []
    if oferta_tabs:
        tab_labels.append("📊 Ofertas de Disciplinas")
    if grade_tabs:
        tab_labels.append("📋 Grades Curriculares")
    
    main_tabs = st.tabs(tab_labels)
    
    # Tab de Ofertas
    if oferta_tabs:
        tab_index = 0
        with main_tabs[tab_index]:
            st.markdown("### 📊 Ofertas por Período")
            
            # Sub-tabs para cada período de oferta
            oferta_subtabs = st.tabs([f"📅 {tab}" for tab in oferta_tabs])
            
            for i, tab_name in enumerate(oferta_tabs):
                with oferta_subtabs[i]:
                    # Carregamento otimizado dos dados de oferta
                    df_oferta_display, color_map, unique_turmas = process_oferta_data(SHEET_ID, tab_name)
                    
                    if not df_oferta_display.empty:
                        # Métricas no topo
                        
                        # Filtros avançados
                        col_search, col_turma = st.columns([2, 1])
                        
                        with col_search:
                            search_term = st.text_input(
                                "🔍 Buscar disciplina ou professor:",
                                placeholder="Digite o nome da disciplina ou professor...",
                                key=f"search_{tab_name}"
                            )
                        
                        with col_turma:
                            if len(unique_turmas) > 1:
                                turma_filter = st.multiselect(
                                    "🎓 Filtrar por turma:",
                                    options=unique_turmas,
                                    default=unique_turmas,
                                    key=f"turma_filter_{tab_name}"
                                )
                            else:
                                turma_filter = unique_turmas
                        
                        # Aplicar filtros
                        df_filtered = df_oferta_display[df_oferta_display['Turma'].isin(turma_filter)]
                        
                        if search_term:
                            # Busca em múltiplas colunas
                            search_columns = ['Disciplina']
                            if 'Professor' in df_filtered.columns:
                                search_columns.append('Professor')
                            
                            mask = df_filtered[search_columns].apply(
                                lambda x: x.astype(str).str.contains(search_term, case=False, na=False)
                            ).any(axis=1)
                            df_filtered = df_filtered[mask]
                        
                        # Aplicar estilo com cache
                        if not df_filtered.empty:
                            styled_oferta = df_filtered.style.apply(style_turma, color_map=color_map, axis=1)
                            cols_to_center = [c for c in df_filtered.columns if c != 'Disciplina']
                            styled_oferta = styled_oferta.set_properties(**{'text-align': 'center'}, subset=cols_to_center)
                            st.dataframe(styled_oferta, use_container_width=True, height=400)
                        else:
                            st.info("🔍 Nenhuma disciplina encontrada para os filtros selecionados.")
                    else:
                        st.info(f"📭 Nenhuma oferta encontrada para o período {tab_name}.")
    
    # Tab de Grades Curriculares
    if grade_tabs:
        tab_index = 1 if oferta_tabs else 0
        with main_tabs[tab_index]:
            st.markdown("### 📋 Grades por Turma")
            
            # Sub-tabs para cada grade
            grade_subtabs = st.tabs([f"🎓 {tab}" for tab in grade_tabs])
            
            for i, tab_name in enumerate(grade_tabs):
                with grade_subtabs[i]:
                    # Carregamento otimizado dos dados de grade
                    df_grade = process_grade_data(SHEET_ID, tab_name)
                    
                    if not df_grade.empty:
                        # Métricas da grade
                        
                        
                        # Filtro de busca para grades
                        if 'Disciplina' in df_grade.columns:
                            search_grade = st.text_input(
                                "🔍 Buscar disciplina na grade:",
                                placeholder="Digite o nome da disciplina...",
                                key=f"search_grade_{tab_name}"
                            )
                            
                            if search_grade:
                                mask_grade = df_grade['Disciplina'].astype(str).str.contains(search_grade, case=False, na=False)
                                df_grade_filtered = df_grade[mask_grade]
                            else:
                                df_grade_filtered = df_grade
                        else:
                            df_grade_filtered = df_grade
                        
                        # Verificar cruzamento com ofertas (se disponível)
                        disciplina_turma_cor = {}
                        if oferta_tabs and 'Disciplina' in df_grade.columns:
                            # Pegar a primeira oferta disponível para referência
                            df_oferta_ref, color_map_ref, _ = process_oferta_data(SHEET_ID, oferta_tabs[0])
                            if not df_oferta_ref.empty:
                                for _, oferta in df_oferta_ref.iterrows():
                                    disciplina = oferta.get('Disciplina')
                                    turma = oferta.get('Turma')
                                    if turma == tab_name and pd.notna(disciplina):
                                        disciplina_turma_cor[disciplina] = color_map_ref.get(turma, "#e3f2fd")
                        
                        # Aplicar estilo se houver cruzamento
                        if disciplina_turma_cor and not df_grade_filtered.empty:
                            styled_grade = df_grade_filtered.style.apply(
                                style_disciplina_turma,
                                disciplina_turma_cor=disciplina_turma_cor,
                                axis=1
                            )
                            st.dataframe(styled_grade, use_container_width=True, height=400)
                            highlighted_count = len([d for d in df_grade_filtered['Disciplina'] if d in disciplina_turma_cor])
                            if highlighted_count > 0:
                                st.success(f"💡 {highlighted_count} disciplina(s) destacada(s) estão sendo ofertadas pela turma {tab_name}")
                        else:
                            st.dataframe(df_grade_filtered, use_container_width=True, height=400)
                    else:
                        st.info(f"📭 Nenhuma disciplina encontrada na grade {tab_name}.")

    

if __name__ == "__main__":
    main()
