from __future__ import annotations

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List

import streamlit as st

# Adicionar diretório raiz ao PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.database.engine import get_db_session, engine
from sqlmodel import Session
import plotly.express as px
import plotly.graph_objects as go

LOGO_PATH = Path(__file__).resolve().parents[2] / "resources" / "fasiOficial.png"


def _render_intro() -> None:
    """Renderiza a introdução da página."""
    st.markdown(
        """
        <style>
            /* Estilos alinhados com identidade visual institucional */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            
            /* Ocultar sidebar completamente */
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
            
            .metric-card {
                background: #ffffff;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                border-left: 4px solid #4a1d7a;
                margin-bottom: 16px;
            }
            
            .metric-card h3 {
                color: #1a0d2e;
                font-size: 1.1rem;
                margin-bottom: 8px;
                font-weight: 600;
            }
            
            .metric-card .metric-value {
                color: #4a1d7a;
                font-size: 2rem;
                font-weight: 700;
                margin: 0;
            }
            
            .status-ativo {
                background-color: #dcfce7;
                color: #166534;
                padding: 4px 8px;
                border-radius: 6px;
                font-size: 0.75rem;
                font-weight: 600;
            }
            
            .status-pendente {
                background-color: #fef3c7;
                color: #78350f;
                padding: 4px 8px;
                border-radius: 6px;
                font-size: 0.75rem;
                font-weight: 600;
            }
            
            .status-encerrado {
                background-color: #fee2e2;
                color: #991b1b;
                padding: 4px 8px;
                border-radius: 6px;
                font-size: 0.75rem;
                font-weight: 600;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    # Logo
    if LOGO_PATH.exists():
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.image(str(LOGO_PATH), width=300)
    
    # Hero Section
    st.markdown(
        """
        <div class="projetos-hero">
            <h1>📊 Consulta de Projetos dos Docentes</h1>
            <p><strong>Visualização e análise de projetos de Ensino, Pesquisa e Extensão</strong></p>
            <p>Acompanhe o status, natureza e detalhes dos projetos submetidos pelos docentes.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _load_projetos_data() -> pd.DataFrame:
    """Carrega dados dos projetos do banco de dados."""
    try:
        query = """
        SELECT 
            id,
            submission_date,
            docente,
            parecerista1,
            parecerista2,
            nome_projeto,
            carga_horaria,
            edital,
            natureza,
            ano_edital,
            solicitacao
        FROM public.projetos_submissions 
        ORDER BY submission_date DESC
        """
        
        with Session(engine) as session:
            df = pd.read_sql(query, session.connection())
        
        # Converter datas para datetime se necessário
        if 'submission_date' in df.columns:
            df['submission_date'] = pd.to_datetime(df['submission_date'])
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at'])
        if 'updated_at' in df.columns:
            df['updated_at'] = pd.to_datetime(df['updated_at'])
            
        return df
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados dos projetos: {e}")
        return pd.DataFrame()


def _render_metrics(df: pd.DataFrame, filtered_df: pd.DataFrame) -> None:
    """Renderiza métricas resumidas dos projetos."""
    if df.empty:
        st.warning("📊 Nenhum projeto encontrado.")
        return
    
    # Todos os 4 cards na mesma linha
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <h3>Total de Projetos</h3>
                <p class="metric-value">{len(filtered_df)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    if 'natureza' in filtered_df.columns:
        # Normalizar valores de natureza para contagem correta
        natureza_values = filtered_df['natureza'].fillna('').str.lower().str.strip()
        
        with col2:
            extensao_count = len(natureza_values[natureza_values.str.contains('extens', na=False)])
            st.markdown(
                f"""
                <div class="metric-card">
                    <h3>Projetos de Extensão</h3>
                    <p class="metric-value">{extensao_count}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        
        with col3:
            pesquisa_count = len(natureza_values[natureza_values.str.contains('pesquisa', na=False)])
            st.markdown(
                f"""
                <div class="metric-card">
                    <h3>Projetos de Pesquisa</h3>
                    <p class="metric-value">{pesquisa_count}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        
        with col4:
            ensino_count = len(natureza_values[natureza_values.str.contains('ensino', na=False)])
            st.markdown(
                f"""
                <div class="metric-card">
                    <h3>Projetos de Ensino</h3>
                    <p class="metric-value">{ensino_count}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )



def _format_status(status: str) -> str:
    """Formata o status com cores."""
    if status == 'ativo':
        return '<span class="status-ativo">Ativo</span>'
    elif status == 'pendente':
        return '<span class="status-pendente">Pendente</span>'
    elif status == 'encerrado':
        return '<span class="status-encerrado">Encerrado</span>'
    else:
        return status


def _render_filters(df: pd.DataFrame) -> Dict[str, Any]:
    """Renderiza filtros e retorna os valores selecionados."""
    st.markdown("### 🔍 Filtros")
    
    col1, col2, col3 = st.columns(3)
    
    filters = {}
    
    with col1:
        # Filtro por docente
        docentes = ['Todos'] + sorted(df['docente'].dropna().unique().tolist()) if 'docente' in df.columns else ['Todos']
        filters['docente'] = st.selectbox(
            "Docente",
            options=docentes,
            key="filter_docente"
        )
    
    with col2:
        # Filtro por natureza
        naturezas = ['Todas'] + sorted(df['natureza'].dropna().unique().tolist()) if 'natureza' in df.columns else ['Todas']
        filters['natureza'] = st.selectbox(
            "Natureza",
            options=naturezas,
            key="filter_natureza"
        )

    with col3:
        # Filtro por ano do edital
        anos = ['Todos']
        if 'ano_edital' in df.columns:
            anos_disponiveis = (
                df['ano_edital']
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
            # Remover N/C e S/D de anos_disponiveis
            anos_disponiveis = [ano for ano in anos_disponiveis if ano != 'N/C' and ano != 'S/D']
            anos = ['Todos'] + sorted(anos_disponiveis)
        filters['ano'] = st.selectbox(
            "Ano",
            options=anos,
            key="filter_ano"
        )
    
    
    
    return filters


def _apply_filters(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    """Aplica filtros ao DataFrame."""
    filtered_df = df.copy()
    
    if filters['docente'] != 'Todos' and 'docente' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['docente'] == filters['docente']]
    
    if filters['natureza'] != 'Todas' and 'natureza' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['natureza'] == filters['natureza']]

    if filters.get('ano') and filters['ano'] != 'Todos' and 'ano_edital' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['ano_edital'].astype(str) == str(filters['ano'])]
    
   
    return filtered_df


def _render_data_table(df: pd.DataFrame) -> None:
    """Renderiza a tabela de dados dos projetos."""
    if df.empty:
        st.info("📋 Nenhum projeto encontrado com os filtros aplicados.")
        return
    
    st.markdown("### 📋 Lista de Projetos")
    
    # Preparar dados para exibição
    display_df = df.copy()
    
    # Formatar datas
    if 'submission_date' in display_df.columns:
        display_df['submission_date'] = display_df['submission_date'].dt.strftime('%d/%m/%Y %H:%M')
    
    # Renomear colunas para exibição
    column_names = {
        'id': 'ID',
        'submission_date': 'Data/Hora',
        'docente': 'Docente',
        'parecerista1': 'Parecerista 1',
        'parecerista2': 'Parecerista 2',
        'nome_projeto': 'Nome do Projeto',
        'carga_horaria': 'Carga Horária',
        'edital': 'Edital',
        'natureza': 'Natureza',
        'ano_edital': 'Ano do Edital',
        'solicitacao': 'Solicitação'
    }
    
    # Selecionar apenas colunas relevantes para exibição
    columns_to_show = ['Docente', 'Nome do Projeto', 
                       'Natureza', 'Edital', 'Solicitação', 'Carga Horária']
    
    display_df = display_df.rename(columns=column_names)
    display_df = display_df[[col for col in columns_to_show if col in display_df.columns]]
    
    # Configurar tabela
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Nome do Projeto": st.column_config.TextColumn(
                "Nome do Projeto",
                help="Título completo do projeto",
                width="large"
            )
        }
    )
    
    # Botão para download
    if not df.empty:
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"projetos_docentes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            help="Baixar dados em formato CSV"
        )


def main() -> None:
    """Função principal da página."""
    st.set_page_config(
        page_title="Consulta Projetos - FasiTech",
        layout="wide",
        page_icon="📊",
        initial_sidebar_state="collapsed",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': None
        }
    )
    
    _render_intro()
    
    # Carregar dados
    with st.spinner("📊 Carregando dados dos projetos..."):
        df = _load_projetos_data()
    
    if df.empty:
        st.error("❌ Nenhum projeto encontrado no banco de dados.")
        st.info("💡 Verifique se há projetos submetidos ou se a conexão com o banco está funcionando.")
        return
    
    # Renderizar filtros
    filters = _render_filters(df)
    
    # Aplicar filtros
    filtered_df = _apply_filters(df, filters)
    
    # Renderizar métricas (4 cards na mesma linha) com dados filtrados
    _render_metrics(df, filtered_df)
    
    st.markdown("---")
    
    # Renderizar tabela
    _render_data_table(filtered_df)
    
    # Botão voltar
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🏠 Voltar ao Menu Principal", use_container_width=True):
            st.switch_page("main.py")


if __name__ == "__main__":
    main()
