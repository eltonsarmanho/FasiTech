# -*- coding: utf-8 -*-
"""
Gestor de Alertas Acadêmicos — FasiTech
========================================
Painel protegido por FASI_TOKEN que permite cadastrar, atualizar, excluir e
disparar manualmente gatilhos de e-mail para docentes.

Acesso: apenas quem possuir o FASI_TOKEN configurado no .env.
"""
from __future__ import annotations

import os
import sys
from datetime import date, datetime, time
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# PYTHONPATH setup
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.utils.env_loader import load_environment

load_environment()

from src.database.repository import (
    create_alerta,
    delete_alerta,
    get_all_alertas,
    get_alerta_by_id,
    update_alerta,
)
from src.services.alert_service import fire_alert

LOGO_PATH = Path(__file__).resolve().parents[2] / "resources" / "fasiOficial.png"

# ---------------------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------------------

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

    .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1100px; }

    /* Hero */
    .alert-hero {
        background: linear-gradient(135deg, #1a0d2e 0%, #2d1650 50%, #4a1d7a 100%);
        border-radius: 16px;
        padding: 36px 40px;
        color: #fff;
        margin-bottom: 32px;
        box-shadow: 0 10px 30px rgba(26,13,46,.25);
        position: relative;
        overflow: hidden;
    }
    .alert-hero::before {
        content: '';
        position: absolute;
        top: -30%; right: -5%;
        width: 300px; height: 300px;
        background: radial-gradient(circle, rgba(255,255,255,.08) 0%, transparent 70%);
        border-radius: 50%;
    }
    .alert-hero h1 { color: #fff; font-size: 2rem; font-weight: 700; margin-bottom: 8px; }
    .alert-hero p  { color: rgba(255,255,255,.85); font-size: 1rem; margin: 0; }

    /* Auth box */
    .auth-box {
        background: #f8fafc;
        border: 2px solid rgba(124,58,237,.25);
        border-radius: 16px;
        padding: 40px;
        max-width: 480px;
        margin: 40px auto;
        text-align: center;
        box-shadow: 0 4px 16px rgba(0,0,0,.06);
    }
    .auth-box h3 { color: #1a0d2e; margin-bottom: 8px; }
    .auth-box p  { color: #64748b; font-size: .95rem; margin-bottom: 24px; }

    /* Alert cards */
    .alerta-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 22px 26px;
        margin-bottom: 18px;
        border-left: 5px solid #7c3aed;
        box-shadow: 0 2px 10px rgba(0,0,0,.07);
        transition: box-shadow .2s ease;
    }
    .alerta-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,.12); }
    .alerta-card-title { font-size: 1.15rem; font-weight: 700; color: #1a0d2e; margin-bottom: 6px; }
    .alerta-card-meta  { font-size: .85rem; color: #64748b; margin-bottom: 10px; }
    .alerta-card-desc  { font-size: .95rem; color: #374151; line-height: 1.6; }
    .badge-ativo   { background: #d1fae5; color: #065f46; padding: 3px 10px; border-radius: 20px; font-size: .8rem; font-weight: 600; }
    .badge-inativo { background: #fee2e2; color: #991b1b; padding: 3px 10px; border-radius: 20px; font-size: .8rem; font-weight: 600; }

    /* Section title */
    .section-title {
        color: #1a0d2e; font-size: 1.6rem; font-weight: 700;
        margin-bottom: 20px; padding-bottom: 10px;
        border-bottom: 3px solid #7c3aed; display: inline-block;
    }

    /* Form card */
    .form-card {
        background: #f8fafc;
        border-radius: 14px;
        padding: 28px;
        border: 1px solid rgba(124,58,237,.15);
        box-shadow: 0 2px 8px rgba(0,0,0,.04);
        margin-bottom: 28px;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
        transition: all .2s ease !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(102,126,234,.4) !important;
    }
</style>
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check_token(input_token: str) -> bool:
    """Valida o token contra FASI_TOKEN do ambiente."""
    fasi_token = os.getenv("FASI_TOKEN", "")
    return bool(fasi_token) and input_token.strip() == fasi_token


def _render_auth_wall() -> bool:
    """
    Exibe a tela de autenticação.

    Returns:
        True se o usuário está autenticado, False caso contrário.
    """
    if st.session_state.get("gestor_alertas_auth"):
        return True

    st.markdown(
        """
        <div class="auth-box">
            <div style="font-size:3rem; margin-bottom:12px;">🔐</div>
            <h3>Acesso Restrito</h3>
            <p>O Gestor de Alertas Acadêmicos é exclusivo para administradores FASI.<br>
            Insira o <strong>FASI_TOKEN</strong> para continuar.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        token_input = st.text_input(
            "🔑 Token de acesso",
            type="password",
            placeholder="Cole o FASI_TOKEN aqui...",
            key="token_input_gestor",
        )
        if st.button("🚀 Entrar", key="btn_entrar_gestor", use_container_width=True):
            if _check_token(token_input):
                st.session_state["gestor_alertas_auth"] = True
                st.rerun()
            else:
                st.error("❌ Token inválido. Verifique o FASI_TOKEN configurado no .env.")

    return False


def _format_date(date_str: str) -> str:
    """Converte 'YYYY-MM-DD' → 'DD/MM/YYYY'."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return date_str


def _alert_status_badge(alerta) -> str:
    today = date.today().isoformat()
    if not alerta.ativo:
        return '<span class="badge-inativo">⏸ Inativo</span>'
    if alerta.data_fim < today:
        return '<span class="badge-inativo">✅ Expirado</span>'
    if alerta.data_inicio > today:
        return '<span class="badge-ativo">⏳ Aguardando início</span>'
    return '<span class="badge-ativo">🟢 Ativo</span>'


# ---------------------------------------------------------------------------
# Painel — Lista de alertas
# ---------------------------------------------------------------------------

def _render_alert_list(alertas: list) -> None:
    if not alertas:
        st.info("📭 Nenhum gatilho de alerta cadastrado ainda.")
        return

    for alerta in alertas:
        ultimo = (
            f"Último disparo: {_format_date(alerta.ultimo_disparo)}"
            if alerta.ultimo_disparo
            else "Nunca disparado"
        )
        badge = _alert_status_badge(alerta)

        st.markdown(
            f"""
            <div class="alerta-card">
                <div class="alerta-card-title">🔔 {alerta.titulo}</div>
                <div class="alerta-card-meta">
                    📅 {_format_date(alerta.data_inicio)} → {_format_date(alerta.data_fim)}
                    &nbsp;|&nbsp;
                    🕐 {alerta.horario_disparo}
                    &nbsp;|&nbsp;
                    {badge}
                    &nbsp;|&nbsp;
                    <em>{ultimo}</em>
                </div>
                <div class="alerta-card-desc">{alerta.descricao[:220]}{'…' if len(alerta.descricao) > 220 else ''}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2, col3, col4 = st.columns([2, 2, 2, 6])
        with col1:
            if st.button("✏️ Editar", key=f"edit_{alerta.id}", use_container_width=True):
                st.session_state["editing_alerta_id"] = alerta.id
                st.rerun()
        with col2:
            if st.button("🗑️ Excluir", key=f"del_{alerta.id}", use_container_width=True):
                st.session_state[f"confirm_del_{alerta.id}"] = True
                st.rerun()
        with col3:
            if st.button("📨 Disparar", key=f"fire_{alerta.id}", use_container_width=True):
                with st.spinner("Enviando e-mails..."):
                    ok, msg = fire_alert(alerta.id)
                if ok:
                    st.success(f"✅ {msg}")
                else:
                    st.error(f"❌ {msg}")
                st.rerun()

        # Confirmação de exclusão
        if st.session_state.get(f"confirm_del_{alerta.id}"):
            st.warning(f"⚠️ Confirma exclusão do alerta **{alerta.titulo}**?")
            cc1, cc2 = st.columns(2)
            with cc1:
                if st.button("✅ Sim, excluir", key=f"confirm_yes_{alerta.id}", use_container_width=True):
                    delete_alerta(alerta.id)
                    st.session_state.pop(f"confirm_del_{alerta.id}", None)
                    st.success("🗑️ Alerta excluído com sucesso.")
                    st.rerun()
            with cc2:
                if st.button("❌ Cancelar", key=f"confirm_no_{alerta.id}", use_container_width=True):
                    st.session_state.pop(f"confirm_del_{alerta.id}", None)
                    st.rerun()

        st.markdown("<hr style='border:none; border-top:1px solid #e2e8f0; margin:4px 0 16px 0;'>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Formulário de criação
# ---------------------------------------------------------------------------

def _render_create_form() -> None:
    st.markdown('<h2 class="section-title">➕ Novo Gatilho de Alerta</h2>', unsafe_allow_html=True)
    st.markdown('<div class="form-card">', unsafe_allow_html=True)

    with st.form("form_criar_alerta", clear_on_submit=True):
        titulo = st.text_input(
            "📌 Título do Gatilho *",
            placeholder="Ex: Prazo de entrega dos Planos de Ensino",
            max_chars=255,
        )
        descricao = st.text_area(
            "📝 Descrição *",
            placeholder="Descreva o alerta em detalhes. Este texto será enviado no corpo do e-mail.",
            height=160,
        )

        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input(
                "📅 Data de Início *",
                value=date.today(),
                min_value=date(2024, 1, 1),
            )
        with col2:
            data_fim = st.date_input(
                "📅 Data de Encerramento *",
                value=date.today(),
                min_value=date(2024, 1, 1),
            )

        horario_disparo = st.time_input(
            "🕐 Horário do Disparo Diário *",
            value=time(8, 0),
            step=60,
        )

        ativo = st.checkbox("✅ Ativar gatilho imediatamente", value=True)

        submitted = st.form_submit_button("💾 Salvar Gatilho", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        errors = []
        if not titulo.strip():
            errors.append("Título é obrigatório.")
        if not descricao.strip():
            errors.append("Descrição é obrigatória.")
        if data_fim < data_inicio:
            errors.append("Data de encerramento deve ser >= data de início.")

        if errors:
            for e in errors:
                st.error(f"❌ {e}")
            return

        try:
            alerta_id = create_alerta({
                "titulo": titulo.strip(),
                "descricao": descricao.strip(),
                "data_inicio": data_inicio.isoformat(),
                "data_fim": data_fim.isoformat(),
                "horario_disparo": horario_disparo.strftime("%H:%M"),
                "ativo": ativo,
            })
            st.success(
                f"✅ Gatilho **{titulo}** criado com sucesso! "
                f"(ID: {alerta_id}) — "
                f"Disparos diários às {horario_disparo.strftime('%H:%M')} "
                f"de {_format_date(data_inicio.isoformat())} "
                f"a {_format_date(data_fim.isoformat())}."
            )
            st.rerun()
        except Exception as exc:
            st.error(f"❌ Erro ao salvar gatilho: {exc}")


# ---------------------------------------------------------------------------
# Formulário de edição
# ---------------------------------------------------------------------------

def _render_edit_form(alerta_id: int) -> None:
    alerta = get_alerta_by_id(alerta_id)
    if alerta is None:
        st.error("❌ Alerta não encontrado.")
        st.session_state.pop("editing_alerta_id", None)
        return

    st.markdown(
        f'<h2 class="section-title">✏️ Editar Gatilho — {alerta.titulo}</h2>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="form-card">', unsafe_allow_html=True)

    with st.form("form_editar_alerta"):
        titulo = st.text_input(
            "📌 Título do Gatilho *",
            value=alerta.titulo,
            max_chars=255,
        )
        descricao = st.text_area(
            "📝 Descrição *",
            value=alerta.descricao,
            height=160,
        )

        try:
            d_inicio = datetime.strptime(alerta.data_inicio, "%Y-%m-%d").date()
        except ValueError:
            d_inicio = date.today()
        try:
            d_fim = datetime.strptime(alerta.data_fim, "%Y-%m-%d").date()
        except ValueError:
            d_fim = date.today()

        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input("📅 Data de Início *", value=d_inicio)
        with col2:
            data_fim_field = st.date_input("📅 Data de Encerramento *", value=d_fim)

        try:
            h, m = map(int, alerta.horario_disparo.split(":"))
            t_default = time(h, m)
        except Exception:
            t_default = time(8, 0)

        horario_disparo = st.time_input(
            "🕐 Horário do Disparo Diário *",
            value=t_default,
            step=60,
        )
        ativo = st.checkbox("✅ Gatilho ativo", value=alerta.ativo)

        col_s, col_c = st.columns(2)
        with col_s:
            submitted = st.form_submit_button("💾 Salvar Alterações", use_container_width=True)
        with col_c:
            cancelled = st.form_submit_button("❌ Cancelar", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if cancelled:
        st.session_state.pop("editing_alerta_id", None)
        st.rerun()

    if submitted:
        errors = []
        if not titulo.strip():
            errors.append("Título é obrigatório.")
        if not descricao.strip():
            errors.append("Descrição é obrigatória.")
        if data_fim_field < data_inicio:
            errors.append("Data de encerramento deve ser >= data de início.")

        if errors:
            for e in errors:
                st.error(f"❌ {e}")
            return

        try:
            update_alerta(alerta_id, {
                "titulo": titulo.strip(),
                "descricao": descricao.strip(),
                "data_inicio": data_inicio.isoformat(),
                "data_fim": data_fim_field.isoformat(),
                "horario_disparo": horario_disparo.strftime("%H:%M"),
                "ativo": ativo,
            })
            st.session_state.pop("editing_alerta_id", None)
            st.success("✅ Gatilho atualizado com sucesso!")
            st.rerun()
        except Exception as exc:
            st.error(f"❌ Erro ao atualizar: {exc}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(
        page_title="Gestor de Alertas Acadêmicos — FASI",
        page_icon="🔔",
        layout="wide",
        initial_sidebar_state="collapsed",
        menu_items={"Get Help": None, "Report a bug": None, "About": None},
    )

    st.markdown(_CSS, unsafe_allow_html=True)

    # Logo
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width="stretch")

    # Hero header
    st.markdown(
        """
        <div class="alert-hero">
            <h1>🔔 Gestor de Alertas Acadêmicos</h1>
            <p>Crie e gerencie gatilhos de e-mail automáticos para docentes da FASI.</p>
            <p>Os alertas são disparados diariamente no horário configurado, durante o intervalo de datas definido.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Verificação de autenticação
    if not _render_auth_wall():
        return

    # Botão de logout discreto
    col_lo, _ = st.columns([1, 9])
    with col_lo:
        if st.button("🔓 Sair", key="btn_logout_gestor"):
            st.session_state.pop("gestor_alertas_auth", None)
            st.rerun()

    # Navegação: se está editando, mostra o form de edição
    editing_id = st.session_state.get("editing_alerta_id")
    if editing_id is not None:
        _render_edit_form(editing_id)
        if st.button("← Voltar à lista", key="btn_back_list"):
            st.session_state.pop("editing_alerta_id", None)
            st.rerun()
        return

    # Abas: Lista | Criar
    tab_list, tab_create = st.tabs(["📋 Gatilhos Cadastrados", "➕ Novo Gatilho"])

    with tab_list:
        st.markdown('<h2 class="section-title">📋 Gatilhos de Alerta</h2>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        try:
            alertas = get_all_alertas()
            total = len(alertas)
            ativos = sum(1 for a in alertas if a.ativo)
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Total de Gatilhos", total)
            col_m2.metric("Ativos", ativos)
            col_m3.metric("Inativos / Expirados", total - ativos)
            st.markdown("<br>", unsafe_allow_html=True)
            _render_alert_list(alertas)
        except Exception as exc:
            st.error(f"❌ Erro ao carregar alertas: {exc}")

    with tab_create:
        _render_create_form()


if __name__ == "__main__":
    main()
