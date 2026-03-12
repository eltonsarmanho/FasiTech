from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Adicionar diretorio raiz ao PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.utils.env_loader import load_environment
from src.database.repository import get_lancamento_conceitos

load_environment()

LOGO_PATH = Path(__file__).resolve().parents[2] / "resources" / "fasiOficial.png"

_CSS = """
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

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1100px;
    }

    .hero {
        background: linear-gradient(135deg, #1a0d2e 0%, #2d1650 50%, #4a1d7a 100%);
        border-radius: 16px;
        padding: 36px 40px;
        color: #fff;
        margin-bottom: 28px;
        box-shadow: 0 10px 30px rgba(26,13,46,.25);
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
        background: radial-gradient(circle, rgba(255,255,255,.08) 0%, transparent 70%);
        border-radius: 50%;
    }

    .hero h1 {
        color: #fff;
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .hero p {
        color: rgba(255,255,255,.9);
        margin: 0;
        font-size: 1rem;
    }

    .auth-box {
        background: #f8fafc;
        border: 2px solid rgba(124,58,237,.25);
        border-radius: 16px;
        padding: 36px;
        max-width: 520px;
        margin: 32px auto;
        text-align: center;
        box-shadow: 0 4px 16px rgba(0,0,0,.06);
    }

    .auth-box h3 {
        color: #1a0d2e;
        margin-bottom: 8px;
    }

    .auth-box p {
        color: #64748b;
        margin-bottom: 22px;
    }

    .filter-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 22px 24px;
        border: 1px solid rgba(124,58,237,.18);
        box-shadow: 0 2px 8px rgba(0,0,0,.04);
        margin-bottom: 18px;
    }

    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(102,126,234,.35) !important;
    }
</style>
"""


def _check_token(input_token: str) -> bool:
    fasi_token = os.getenv("FASI_TOKEN", "")
    return bool(fasi_token) and input_token.strip() == fasi_token


def _render_auth_wall() -> bool:
    if st.session_state.get("lancamento_conceitos_auth"):
        return True

    st.markdown(
        """
        <div class="auth-box">
            <div style="font-size:3rem; margin-bottom:12px;">🔐</div>
            <h3>Acesso Restrito</h3>
            <p>Insira o <strong>FASI_TOKEN</strong> para acessar o painel de Lancamento de Conceitos.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        token_input = st.text_input(
            "Token de acesso",
            type="password",
            placeholder="Cole o FASI_TOKEN aqui...",
            key="token_input_lancamento",
        )
        if st.button("Entrar", key="btn_entrar_lancamento", use_container_width=True):
            if _check_token(token_input):
                st.session_state["lancamento_conceitos_auth"] = True
                st.rerun()
            st.error("Token invalido. Verifique o FASI_TOKEN configurado no .env.")

        if st.button("Voltar ao Portal", key="btn_voltar_lancamento_auth", use_container_width=True):
            st.switch_page("main.py")

    return False


def _build_filter_options(rows: list[dict[str, str]], field: str, all_label: str = "Todos") -> list[str]:
    values = sorted({_safe_text(row.get(field, "")) for row in rows if _safe_text(row.get(field, ""))})
    return [all_label] + values


def _safe_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _render_table(rows: list[dict[str, str]]) -> None:
    if not rows:
        st.info("Nenhum aluno encontrado com os filtros aplicados.")
        return

    df = pd.DataFrame(rows)
    show_df = df.rename(
        columns={
            "matricula": "Matricula",
            "periodo": "Periodo",
            "polo": "Polo",
            "turma": "Turma",
            "componente": "Componente",
        }
    )

    ordered_cols = ["Matricula", "Periodo", "Polo", "Turma", "Componente"]
    ordered_cols = [col for col in ordered_cols if col in show_df.columns]

    st.dataframe(show_df[ordered_cols], use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(
        page_title="Lancamento de Conceitos - FasiTech",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="collapsed",
        menu_items={"Get Help": None, "Report a bug": None, "About": None},
    )

    st.markdown(_CSS, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width="stretch")

    st.markdown(
        """
        <div class="hero">
            <h1>📝 Lancamento de Conceitos</h1>
            <p>Selecione ACC, TCC ou Estagio e aplique filtros por Turma, Polo e Periodo.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not _render_auth_wall():
        return

    col_logout, col_back, _ = st.columns([1, 1, 6])
    with col_logout:
        if st.button("Sair", key="btn_logout_lancamento", use_container_width=True):
            st.session_state.pop("lancamento_conceitos_auth", None)
            st.rerun()
    with col_back:
        if st.button("Voltar", key="btn_voltar_lancamento", use_container_width=True):
            st.switch_page("main.py")

    st.markdown("<div class='filter-card'>", unsafe_allow_html=True)

    tipo_formulario = st.radio(
        "Tipo de lancamento",
        options=["ACC", "TCC", "Estagio"],
        horizontal=True,
    )

    componente_estagio = "Todos"
    if tipo_formulario == "Estagio":
        componente_estagio = st.selectbox(
            "Componente de Estagio",
            options=[
                "Todos",
                "Plano de Estágio (Estágio I)",
                "Relatório Final (Estágio II)",
            ],
        )

    rows_base = get_lancamento_conceitos(
        tipo_formulario=tipo_formulario,
        componente_estagio=None if componente_estagio == "Todos" else componente_estagio,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        turma_sel = st.selectbox("Turma", options=_build_filter_options(rows_base, "turma", "Todas"))
    with col2:
        polo_sel = st.selectbox("Polo", options=_build_filter_options(rows_base, "polo", "Todos"))
    with col3:
        periodo_sel = st.selectbox("Periodo", options=_build_filter_options(rows_base, "periodo", "Todos"))

    st.markdown("</div>", unsafe_allow_html=True)

    rows = get_lancamento_conceitos(
        tipo_formulario=tipo_formulario,
        turma=None if turma_sel == "Todas" else turma_sel,
        polo=None if polo_sel == "Todos" else polo_sel,
        periodo=None if periodo_sel == "Todos" else periodo_sel,
        componente_estagio=None if componente_estagio == "Todos" else componente_estagio,
    )

    st.metric("Total de alunos encontrados", len(rows))
    st.markdown("### Dados para Lancamento")
    _render_table(rows)


if __name__ == "__main__":
    main()
