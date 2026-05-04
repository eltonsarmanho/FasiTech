from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from sqlmodel import Session

# Adicionar diretório raiz ao PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.database.engine import engine

LOGO_PATH = Path(__file__).resolve().parents[2] / "resources" / "fasiOficial.png"


def _render_intro() -> None:
    st.markdown(
        """
        <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}

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

            .hero {
                background: linear-gradient(135deg, #1a0d2e 0%, #2d1650 50%, #4a1d7a 100%);
                border-radius: 16px;
                padding: 36px;
                color: #ffffff;
                margin-bottom: 32px;
                box-shadow: 0 10px 30px rgba(26, 13, 46, 0.25);
                position: relative;
                overflow: hidden;
            }

            .hero::before {
                content: '';
                position: absolute;
                top: -30%;
                right: -5%;
                width: 300px;
                height: 300px;
                background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
                border-radius: 50%;
            }

            .hero h1 {
                font-size: 1.9rem;
                margin-bottom: 16px;
                font-weight: 700;
                text-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }

            .hero p {
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
        </style>
        """,
        unsafe_allow_html=True,
    )

    if LOGO_PATH.exists():
        c1, c2, c3 = st.columns([1, 1, 1])
        with c2:
            st.image(str(LOGO_PATH), width=300)

    st.markdown(
        """
        <div class="hero">
            <h1>📋 Consulta de Requerimento TCC</h1>
            <p><strong>Visualização de dados submetidos de requerimento de TCC</strong></p>
            <p>Acompanhe submissões por aluno, orientador e modalidade.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _load_requerimentos_data() -> pd.DataFrame:
    try:
        query = """
        SELECT *
        FROM public.requerimento_tcc_submissions
        ORDER BY submission_date DESC
        """
        with Session(engine) as session:
            df = pd.read_sql(query, session.connection())

        if "submission_date" in df.columns:
            df["submission_date"] = pd.to_datetime(df["submission_date"], errors="coerce")
        return df
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados de Requerimento TCC: {e}")
        return pd.DataFrame()


def _render_metrics(filtered_df: pd.DataFrame) -> None:
    if filtered_df.empty:
        st.warning("📊 Nenhum requerimento encontrado.")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <h3>Total de Requerimentos</h3>
                <p class="metric-value">{len(filtered_df)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    modalidades = filtered_df["modalidade"].dropna().nunique() if "modalidade" in filtered_df.columns else 0
    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <h3>Modalidades</h3>
                <p class="metric-value">{modalidades}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    orientadores = filtered_df["orientador"].dropna().nunique() if "orientador" in filtered_df.columns else 0
    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <h3>Orientadores</h3>
                <p class="metric-value">{orientadores}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    ultima_data = "-"
    if "submission_date" in filtered_df.columns and not filtered_df["submission_date"].isna().all():
        ultima_data = filtered_df["submission_date"].max().strftime("%d/%m/%Y")
    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <h3>Última Submissão</h3>
                <p class="metric-value" style="font-size:1.2rem;">{ultima_data}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_table(filtered_df: pd.DataFrame) -> None:
    if filtered_df.empty:
        st.info("📋 Nenhum dado encontrado com os filtros aplicados.")
        return

    st.markdown("### 📋 Dados Submetidos")
    show_df = filtered_df.copy()

    if "submission_date" in show_df.columns:
        show_df["submission_date"] = show_df["submission_date"].dt.strftime("%d/%m/%Y %H:%M")

    rename_map = {
        "nome_aluno": "Nome",
        "matricula": "Matrícula",
        "titulo_trabalho": "Título",
        "modalidade": "Modalidade",
        "orientador": "Orientador",
        "submission_date": "Data/Hora",
    }
    show_df = show_df.rename(columns=rename_map)

    ordered_columns = ["Nome", "Matrícula", "Título", "Modalidade", "Orientador", "Data/Hora"]
    ordered_columns = [c for c in ordered_columns if c in show_df.columns]
    show_df = show_df[ordered_columns]

    st.dataframe(show_df, use_container_width=True, hide_index=True)


def _build_download_df(filtered_df: pd.DataFrame) -> pd.DataFrame:
    df = filtered_df.copy()
    palavra_chave_series = df.get("palavra_chave", df.get("palavras_chave", ""))
    return pd.DataFrame(
        {
            "nome": df.get("nome_aluno", ""),
            "matricula": df.get("matricula", ""),
            "email": df.get("email", ""),
            "titulo": df.get("titulo_trabalho", ""),
            "resumo": df.get("resumo", ""),
            "palavras_chave": palavra_chave_series,
            "data_defesa": df.get("data_defesa", ""),
            "modalidade": df.get("modalidade", ""),
            "orientador": df.get("orientador", ""),
            "membro1": df.get("membro_banca1", ""),
            "membro1_outro": df.get("membro1_outro", ""),
            "membro2": df.get("membro_banca2", ""),
            "membro2_outro": df.get("membro2_outro", ""),
            "membro3": df.get("membro3", ""),
            "membro3_outro": df.get("membro3_outro", ""),
        }
    )


def main() -> None:
    st.set_page_config(
        page_title="Consulta Requerimento TCC - FasiTech",
        layout="wide",
        page_icon="📋",
        initial_sidebar_state="collapsed",
        menu_items={"Get Help": None, "Report a bug": None, "About": None},
    )

    _render_intro()

    with st.spinner("📊 Carregando dados de Requerimento TCC..."):
        df = _load_requerimentos_data()

    if df.empty:
        st.error("❌ Nenhum requerimento encontrado no banco de dados.")
        return

    orientadores = ["Todos"] + sorted(df["orientador"].dropna().unique().tolist()) if "orientador" in df.columns else ["Todos"]
    modalidades = ["Todas"] + sorted(df["modalidade"].dropna().unique().tolist()) if "modalidade" in df.columns else ["Todas"]
    c1, c2 = st.columns(2)
    with c1:
        filtro_orientador = st.selectbox("Orientador", orientadores)
    with c2:
        filtro_modalidade = st.selectbox("Modalidade", modalidades)

    filtered_df = df.copy()
    if filtro_orientador != "Todos" and "orientador" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["orientador"] == filtro_orientador]
    if filtro_modalidade != "Todas" and "modalidade" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["modalidade"] == filtro_modalidade]

    if "submission_date" in filtered_df.columns:
        filtered_df = filtered_df.sort_values(by="submission_date", ascending=False)

    _render_metrics(filtered_df)
    st.markdown("---")
    _render_table(filtered_df)

    download_df = _build_download_df(filtered_df)
    csv = download_df.to_csv(index=False)
    st.download_button(
        label="📥 Baixar Dados Completos (CSV)",
        data=csv,
        file_name=f"requerimento_tcc_completo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        help="Baixa os dados completos de Requerimento TCC do banco.",
    )

    st.markdown("---")
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        if st.button("🏠 Voltar ao Menu Principal", use_container_width=True):
            st.switch_page("main.py")


if __name__ == "__main__":
    main()
