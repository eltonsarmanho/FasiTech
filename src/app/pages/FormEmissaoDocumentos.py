from __future__ import annotations

import re
import sys
import time
from pathlib import Path
from typing import Any

import streamlit as st

# Adicionar diretório raiz ao PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.services.document_emission_service import (
    DOCUMENTO_CONCLUSAO,
    DOCUMENTO_MATRICULA,
    process_document_emission_submission,
)

LOGO_PATH = Path(__file__).resolve().parents[2] / "resources" / "fasiOficial.png"
MAX_FILE_SIZE_MB = 50


def _load_settings() -> dict[str, Any]:
    """Resgata configurações de envio de e-mail para emissão de documentos."""
    try:
        settings = st.secrets.get("emissao_documentos", {}) if hasattr(st, "secrets") else {}
    except FileNotFoundError:
        settings = {}
    except Exception:
        settings = {}

    recipients = settings.get("notification_recipients", [])
    if isinstance(recipients, str):
        recipients = [email.strip() for email in recipients.split(",") if email.strip()]
    return {"notification_recipients": recipients}


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

            .docs-hero {
                background: linear-gradient(135deg, #1a0d2e 0%, #2d1650 50%, #4a1d7a 100%);
                border-radius: 16px;
                padding: 36px;
                color: #ffffff;
                margin-bottom: 32px;
                box-shadow: 0 10px 30px rgba(26, 13, 46, 0.25);
                position: relative;
                overflow: hidden;
            }

            .docs-hero::before {
                content: '';
                position: absolute;
                top: -30%;
                right: -5%;
                width: 300px;
                height: 300px;
                background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
                border-radius: 50%;
            }

            .docs-hero h1 {
                font-size: 1.9rem;
                margin-bottom: 16px;
                font-weight: 700;
                text-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }

            .docs-required {
                color: #ef4444;
                font-weight: 700;
            }

            .stButton > button {
                width: 100%;
                background: linear-gradient(135deg, #4a1d7a 0%, #7c3aed 100%);
                color: #ffffff;
                border: none;
                font-weight: 600;
                padding: 16px 32px;
                border-radius: 12px;
                transition: all 0.3s ease;
                font-size: 1rem;
                text-transform: uppercase;
                letter-spacing: 0.5px;
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

    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width="stretch")

    st.markdown(
        f"""
        <div class="docs-hero">
            <h1>📄 Emissão de Documentos</h1>
            <p style="font-size: 1rem; margin-bottom: 12px;">
                Solicite comprovantes acadêmicos com validação automática do histórico.
            </p>
            <ol style="margin-top: 12px; padding-left: 20px; line-height: 1.7;">
                <li>Informe matrícula, CPF e e-mail para envio do comprovante.</li>
                <li>Selecione o tipo de documento desejado.</li>
                <li>Anexe <strong>um único PDF do histórico acadêmico</strong> (máx. {MAX_FILE_SIZE_MB} MB).</li>
            </ol>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def _validate_matricula(matricula: str) -> bool:
    return bool(re.fullmatch(r"\d{12}", matricula))


def _validate_cpf(cpf: str) -> bool:
    digits = re.sub(r"\D", "", cpf or "")
    return len(digits) == 11


def _validate_submission(
    registration: str,
    cpf: str,
    email: str,
    document_type: str,
    uploaded_file: Any,
) -> list[str]:
    errors: list[str] = []

    if not registration.strip():
        errors.append("Matrícula é obrigatória.")
    elif not _validate_matricula(registration):
        errors.append("Matrícula deve conter exatamente 12 dígitos numéricos.")

    if not email.strip():
        errors.append("E-mail é obrigatório.")
    elif not _validate_email(email):
        errors.append("E-mail inválido. Use um formato válido (exemplo@ufpa.br).")

    if not cpf.strip():
        errors.append("CPF é obrigatório.")
    elif not _validate_cpf(cpf):
        errors.append("CPF inválido. Informe 11 dígitos (com ou sem pontuação).")

    if document_type not in {DOCUMENTO_CONCLUSAO, DOCUMENTO_MATRICULA}:
        errors.append("Selecione um tipo de documento válido.")

    if uploaded_file is None:
        errors.append("Anexo do histórico acadêmico é obrigatório.")
    else:
        if uploaded_file.type != "application/pdf":
            errors.append("Apenas arquivo PDF é aceito.")
        max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
        if uploaded_file.size and uploaded_file.size > max_bytes:
            errors.append(f"O arquivo excede o limite de {MAX_FILE_SIZE_MB} MB.")

    return errors


def render_form() -> None:
    _render_intro()
    config = _load_settings()

    with st.form("formulario_emissao_documentos"):
        st.markdown("<span class='docs-required'>*</span> Campo obrigatório", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        registration = col1.text_input(
            "Matrícula *",
            placeholder="202312345678",
            max_chars=12,
            help="Informe sua matrícula com 12 dígitos.",
        )
        cpf = col2.text_input(
            "CPF *",
            placeholder="000.000.000-00",
            max_chars=14,
            help="Este CPF será inserido no comprovante emitido.",
        )
        col3, col4 = st.columns(2)
        email = col3.text_input(
            "E-mail para envio *",
            placeholder="seuemail@ufpa.br",
            help="O comprovante assinado será enviado para este e-mail.",
        )

        document_type = col4.selectbox(
            "Tipo de comprovante *",
            options=[DOCUMENTO_CONCLUSAO, DOCUMENTO_MATRICULA],
            help="Escolha o documento a ser emitido após a validação do histórico.",
        )

        uploaded_file = st.file_uploader(
            "Histórico acadêmico (PDF) *",
            type=["pdf"],
            accept_multiple_files=False,
            help=f"Envie um único PDF do histórico acadêmico (máximo {MAX_FILE_SIZE_MB} MB).",
        )

        col_submit, col_back = st.columns([1, 1])
        with col_submit:
            submitted = st.form_submit_button("Emitir e Enviar Documento", width="stretch")
        with col_back:
            if st.form_submit_button("🏠 Voltar ao Menu Principal", width="stretch"):
                st.switch_page("main.py")

    if not submitted:
        return

    if "docs_processing" not in st.session_state:
        st.session_state.docs_processing = False

    if st.session_state.docs_processing:
        st.warning("Uma emissão já está em andamento. Aguarde.")
        return

    st.session_state.docs_processing = True
    errors = _validate_submission(registration, cpf, email, document_type, uploaded_file)
    if errors:
        st.error("\n".join(f"• {error}" for error in errors))
        st.session_state.docs_processing = False
        return

    with st.spinner("📤 Validando histórico e gerando comprovante..."):
        try:
            result = process_document_emission_submission(
                {
                    "registration": registration,
                    "cpf": cpf,
                    "email": email,
                    "document_type": document_type,
                },
                uploaded_file,
                notification_recipients=config["notification_recipients"],
            )
        except Exception as exc:
            st.error("Não foi possível concluir a emissão. Tente novamente em instantes.")
            st.exception(exc)
            st.session_state.docs_processing = False
            return

    st.session_state.docs_processing = False

    if not result.get("success"):
        st.error(result.get("message", "Solicitação negada após validação do histórico."))
        return

    st.success("✅ Documento emitido com sucesso.")
    st.info(result.get("message", "Comprovante enviado por e-mail."))

    wait_seconds = 3
    try:
        wait_seconds = int(st.secrets.get("sistema", {}).get("timer", 3))
    except Exception:
        wait_seconds = 3
    time.sleep(wait_seconds)
    st.switch_page("main.py")


def main() -> None:
    st.set_page_config(
        page_title="Emissão de Documentos",
        layout="centered",
        page_icon="📄",
        initial_sidebar_state="collapsed",
        menu_items={"Get Help": None, "Report a bug": None, "About": None},
    )
    render_form()


main()
