from __future__ import annotations

import asyncio
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
from src.database.repository import (
    get_lancamento_conceitos,
    update_lancamento_conceitos_status,
)
from src.services.lancamento_service import LancamentoService, ResultadoOperacao

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
            <p>Insira o <strong>FASI_TOKEN</strong> para acessar o painel de Lançamento de Conceitos.</p>
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


def _build_filter_options(rows: list[dict[str, object]], field: str, all_label: str = "Todos") -> list[str]:
    values = sorted({_safe_text(row.get(field, "")) for row in rows if _safe_text(row.get(field, ""))})
    return [all_label] + values


def _safe_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _render_table(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    if not rows:
        st.info("Nenhum aluno encontrado com os filtros aplicados.")
        return []

    df = pd.DataFrame(rows).copy()
    df["selecionar"] = False
    df["matriculado"] = df["matriculado"].fillna(False).astype(bool)
    df["consolidado"] = df["consolidado"].fillna(False).astype(bool)

    show_df = df.rename(
        columns={
            "id": "ID",
            "matricula": "Matricula",
            "periodo": "Periodo",
            "polo": "Polo",
            "turma": "Turma",
            "componente": "Componente",
            "selecionar": "Selecionar",
            "matriculado": "Matriculado",
            "consolidado": "Consolidado",
        }
    )

    ordered_cols = ["ID", "Matricula", "Periodo", "Polo", "Turma", "Componente", "Selecionar", "Matriculado", "Consolidado"]
    ordered_cols = [col for col in ordered_cols if col in show_df.columns]
    editor_df = show_df[ordered_cols]

    edited_df = st.data_editor(
        editor_df,
        use_container_width=True,
        hide_index=True,
        key="editor_lancamento_conceitos",
        disabled=["ID", "Matricula", "Periodo", "Polo", "Turma", "Componente"],
        column_config={
            "ID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "Selecionar": st.column_config.CheckboxColumn("Selecionar"),
            "Matriculado": st.column_config.CheckboxColumn("Matriculado"),
            "Consolidado": st.column_config.CheckboxColumn("Consolidado"),
        },
    )

    selected_df = edited_df[edited_df["Selecionar"] == True]
    selected_rows = [
        {
            "id": int(row["ID"]),
            "matricula": _safe_text(row["Matricula"]),
            "periodo": _safe_text(row["Periodo"]),
            "polo": _safe_text(row["Polo"]),
            "componente": _safe_text(row["Componente"]),
            "matriculado": bool(row["Matriculado"]),
            "consolidado": bool(row["Consolidado"]),
        }
        for _, row in selected_df.iterrows()
    ]

    if selected_rows:
        st.info(
            "Matrículas selecionadas: "
            + ", ".join(item["matricula"] for item in selected_rows)
        )
        st.caption(
            "Componentes selecionados: "
            + ", ".join(sorted({item["componente"] for item in selected_rows}))
        )

    if st.button("Salvar Alteracoes", key="btn_salvar_lancamento_conceitos", use_container_width=False):
        updates: list[dict[str, object]] = []
        for _, row in edited_df.iterrows():
            original_row = editor_df[editor_df["ID"] == row["ID"]].iloc[0]
            if (
                bool(row["Matriculado"]) != bool(original_row["Matriculado"])
                or bool(row["Consolidado"]) != bool(original_row["Consolidado"])
            ):
                updates.append(
                    {
                        "id": int(row["ID"]),
                        "matriculado": bool(row["Matriculado"]),
                        "consolidado": bool(row["Consolidado"]),
                    }
                )

        if not updates:
            st.info("Nenhuma alteracao para salvar.")
            return

        try:
            updated, ignored = update_lancamento_conceitos_status(updates)
            if updated:
                st.success(f"✅ {updated} registro(s) atualizado(s) com sucesso.")
            if ignored:
                st.warning(f"⚠️ {ignored} registro(s) nao puderam ser atualizados.")
            st.rerun()
        except Exception as exc:
            st.error(f"❌ Erro ao salvar alteracoes: {exc}")
    return selected_rows


def _run_async(coro: object) -> ResultadoOperacao:
    return asyncio.run(coro)


def _is_non_blocking_matricula_error(resultado: ResultadoOperacao) -> bool:
    """Define erros de matrícula que não devem interromper o loop de ACC."""
    msg = _safe_text(resultado.mensagem).lower()
    return (
        "esperava dados_registro.jsf" in msg
        and "busca_atividade.jsf" in msg
    )


def _is_non_blocking_consolidacao_error(resultado: ResultadoOperacao) -> bool:
    """Define erros de consolidação que não devem interromper o loop de ACC."""
    msg = _safe_text(resultado.mensagem).lower()
    return (
        "nao encontrou matricula" in msg
        and "na lista" in msg
    )


def _resolve_sigaa_components(componente: object) -> list[str]:
    comp = _safe_text(componente).upper()
    if comp == "ACC":
        return ["ACC I", "ACC II", "ACC III", "ACC IV"]
    if comp in {"ACC I", "ACC II", "ACC III", "ACC IV", "TCC I", "TCC II"}:
        return [comp]
    if comp in {"TCC 1", "TCC1"}:
        return ["TCC I"]
    if comp in {"TCC 2", "TCC2"}:
        return ["TCC II"]
    return []


def _build_lancamento_service(selected: dict[str, object], componente_sigaa: str) -> LancamentoService | None:
    try:
        return LancamentoService(
            matricula=_safe_text(selected.get("matricula")),
            polo=_safe_text(selected.get("polo")),
            periodo=_safe_text(selected.get("periodo")),
            componente=componente_sigaa,
        )
    except Exception as exc:
        st.error(f"❌ Dados inválidos para iniciar serviço de lançamento: {exc}")
        return None


def _render_sigaa_actions(selected_rows: list[dict[str, object]]) -> None:
    if not selected_rows:
        return

    selected = selected_rows[0]
    if len(selected_rows) > 1:
        st.warning("Mais de uma matrícula selecionada. A ação será aplicada à primeira da lista.")

    componentes_sigaa = _resolve_sigaa_components(selected.get("componente"))
    if not componentes_sigaa:
        st.error("❌ Componente não suportado para automação no SIGAA.")
        return

    st.caption(
        f"Matrícula selecionada: {_safe_text(selected.get('matricula'))} | "
        f"Componente: {_safe_text(selected.get('componente'))} | "
        f"SIGAA: {', '.join(componentes_sigaa)} | "
        f"Matriculado: {bool(selected.get('matriculado'))} | "
        f"Consolidado: {bool(selected.get('consolidado'))}"
    )

    c1, c2, c3 = st.columns(3)
    btn_matricular = c1.button("Matricular", key="btn_sigaa_matricular", use_container_width=True)
    btn_consolidar = c2.button("Consolidar", key="btn_sigaa_consolidar", use_container_width=True)
    btn_ambos = c3.button("Matricular/Consolidar", key="btn_sigaa_ambos", use_container_width=True)

    def _update_status_db(matriculado: bool, consolidado: bool) -> None:
        update_lancamento_conceitos_status(
            [
                {
                    "id": int(selected["id"]),
                    "matriculado": matriculado,
                    "consolidado": consolidado,
                }
            ]
        )

    if btn_matricular:
        if bool(selected.get("matriculado")):
            st.info("Matrícula já está marcada como concluída. Operação não executada.")
            return

        houve_falha_bloqueante = False
        for comp_sigaa in componentes_sigaa:
            svc = _build_lancamento_service(selected, comp_sigaa)
            if svc is None:
                return
            with st.spinner(f"Executando matrícula no SIGAA ({comp_sigaa})..."):
                try:
                    resultado = _run_async(svc.matricular())
                except Exception as exc:
                    st.error(f"❌ Erro ao iniciar serviço de matrícula ({comp_sigaa}): {exc}")
                    return
            if not resultado.sucesso:
                if _is_non_blocking_matricula_error(resultado):
                    st.warning(
                        f"⚠️ {comp_sigaa}: já matriculado/anteriormente processado. "
                        "Continuando para o próximo componente."
                    )
                    continue
                st.error(resultado.mensagem)
                houve_falha_bloqueante = True
                break
            st.success(resultado.mensagem)

        if not houve_falha_bloqueante:
            _update_status_db(matriculado=True, consolidado=bool(selected.get("consolidado")))
            st.rerun()

    if btn_consolidar:
        if bool(selected.get("consolidado")):
            st.info("Consolidação já está marcada como concluída. Operação não executada.")
            return

        houve_falha_bloqueante = False
        for comp_sigaa in componentes_sigaa:
            svc = _build_lancamento_service(selected, comp_sigaa)
            if svc is None:
                return
            with st.spinner(f"Executando consolidação no SIGAA ({comp_sigaa})..."):
                try:
                    resultado = _run_async(svc.consolidar(conceito="E"))
                except Exception as exc:
                    st.error(f"❌ Erro ao iniciar serviço de consolidação ({comp_sigaa}): {exc}")
                    return
            if not resultado.sucesso:
                if _is_non_blocking_consolidacao_error(resultado):
                    st.warning(
                        f"⚠️ {comp_sigaa}: não encontrado para consolidar (provavelmente já consolidado). "
                        "Continuando para o próximo componente."
                    )
                    continue
                st.error(resultado.mensagem)
                houve_falha_bloqueante = True
                break
            st.success(resultado.mensagem)

        if not houve_falha_bloqueante:
            _update_status_db(matriculado=bool(selected.get("matriculado")), consolidado=True)
            st.rerun()

    if btn_ambos:
        matriculado_atual = bool(selected.get("matriculado"))
        consolidado_atual = bool(selected.get("consolidado"))

        if not matriculado_atual:
            houve_falha_bloqueante = False
            for comp_sigaa in componentes_sigaa:
                svc = _build_lancamento_service(selected, comp_sigaa)
                if svc is None:
                    return
                with st.spinner(f"Executando matrícula no SIGAA ({comp_sigaa})..."):
                    try:
                        resultado_mat = _run_async(svc.matricular())
                    except Exception as exc:
                        st.error(f"❌ Erro ao iniciar serviço de matrícula ({comp_sigaa}): {exc}")
                        return
                if not resultado_mat.sucesso:
                    if _is_non_blocking_matricula_error(resultado_mat):
                        st.warning(
                            f"⚠️ {comp_sigaa}: já matriculado/anteriormente processado. "
                            "Continuando para o próximo componente."
                        )
                        continue
                    st.error(resultado_mat.mensagem)
                    houve_falha_bloqueante = True
                    break
                st.success(resultado_mat.mensagem)
            if houve_falha_bloqueante:
                return
            matriculado_atual = True
        else:
            st.info("Matrícula já estava concluída. Pulando etapa de matrícula.")

        if not consolidado_atual:
            houve_falha_bloqueante = False
            for comp_sigaa in componentes_sigaa:
                svc = _build_lancamento_service(selected, comp_sigaa)
                if svc is None:
                    _update_status_db(matriculado=matriculado_atual, consolidado=consolidado_atual)
                    return
                with st.spinner(f"Executando consolidação no SIGAA ({comp_sigaa})..."):
                    try:
                        resultado_con = _run_async(svc.consolidar(conceito="E"))
                    except Exception as exc:
                        _update_status_db(matriculado=matriculado_atual, consolidado=consolidado_atual)
                        st.error(f"❌ Erro ao iniciar serviço de consolidação ({comp_sigaa}): {exc}")
                        return
                if not resultado_con.sucesso:
                    if _is_non_blocking_consolidacao_error(resultado_con):
                        st.warning(
                            f"⚠️ {comp_sigaa}: não encontrado para consolidar (provavelmente já consolidado). "
                            "Continuando para o próximo componente."
                        )
                        continue
                    _update_status_db(matriculado=matriculado_atual, consolidado=consolidado_atual)
                    st.error(resultado_con.mensagem)
                    houve_falha_bloqueante = True
                    break
                st.success(resultado_con.mensagem)
            if houve_falha_bloqueante:
                return
            consolidado_atual = True
        else:
            st.info("Consolidação já estava concluída. Pulando etapa de consolidação.")

        _update_status_db(matriculado=matriculado_atual, consolidado=consolidado_atual)
        st.success("✅ Status atualizado no banco de dados.")
        st.rerun()


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

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        turma_sel = st.selectbox("Turma", options=_build_filter_options(rows_base, "turma", "Todas"))
    with col2:
        polo_sel = st.selectbox("Polo", options=_build_filter_options(rows_base, "polo", "Todos"))
    with col3:
        periodo_sel = st.selectbox("Periodo", options=_build_filter_options(rows_base, "periodo", "Todos"))
    with col4:
        matricula_sel = st.selectbox("Matricula", options=_build_filter_options(rows_base, "matricula", "Todas"))
    somente_pendentes = st.checkbox(
        "Somente pendentes (Matriculado=False ou Consolidado=False)",
        value=False,
    )

    rows = get_lancamento_conceitos(
        tipo_formulario=tipo_formulario,
        turma=None if turma_sel == "Todas" else turma_sel,
        polo=None if polo_sel == "Todos" else polo_sel,
        periodo=None if periodo_sel == "Todos" else periodo_sel,
        componente_estagio=None if componente_estagio == "Todos" else componente_estagio,
    )

    if matricula_sel != "Todas":
        rows = [row for row in rows if _safe_text(row.get("matricula")) == matricula_sel]

    if somente_pendentes:
        rows = [
            row
            for row in rows
            if not bool(row.get("matriculado")) or not bool(row.get("consolidado"))
        ]

    st.metric("Total de alunos encontrados", len(rows))
    st.markdown("### Dados para Lancamento")
    selected_rows = _render_table(rows)
    _render_sigaa_actions(selected_rows)


if __name__ == "__main__":
    main()
