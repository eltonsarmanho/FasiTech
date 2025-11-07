"""
Página do Diretor Virtual - Chatbot sobre o PPC.
Interface inspirada em assistentes modernos, mantendo a identidade visual FasiTech.
"""

from __future__ import annotations

import streamlit as st
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import time

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.rag_ppc import PPCChatbotService, get_ppc_service

# Caminhos e identidade visual ------------------------------------------------
LOGO_PATH = PROJECT_ROOT / "src" / "resources" / "fasiOficial.png"

# Sugestões de perguntas rápidas
SUGGESTIONS = [
    {
        "label": "🎯 Objetivo do curso",
        "question": "Qual é o objetivo do curso de Sistemas de Informação?",
    },
    {
        "label": "📚 Disciplinas iniciais",
        "question": "Quais são as disciplinas ofertadas no primeiro período?",
    },
    {
        "label": "🕒 Carga horária",
        "question": "Qual a carga horária total do curso e como ela é distribuída?",
    },
    {
        "label": "📄 Estágio obrigatório",
        "question": "Quantas horas de estágio são obrigatórias no PPC?",
    },
    {
        "label": "🧠 Competências",
        "question": "Quais competências o curso busca desenvolver nos estudantes?",
    },
    {
        "label": "📑 TCC",
        "question": "Como funciona o Trabalho de Conclusão de Curso segundo o PPC?",
    },
]

MIN_TIME_BETWEEN_REQUESTS = timedelta(seconds=3)
WELCOME_MESSAGE = (
    "Olá! Eu sou o Diretor Virtual da FasiTech. Estou pronto para responder "
    "suas dúvidas sobre o Projeto Pedagógico do Curso de Sistemas de Informação."
)

ppc_service: Optional[PPCChatbotService] = None


# Utilitários -----------------------------------------------------------------

def _get_service() -> PPCChatbotService:
    """Retorna a instância singleton do serviço RAG."""
    global ppc_service
    if ppc_service is None:
        ppc_service = get_ppc_service()
    return ppc_service


def _inject_global_styles() -> None:
    """Aplica estilos customizados, mantendo a identidade FasiTech."""
    st.markdown(
        """
        <style>
            :root {
                --fasi-primary: #4a1d7a;
                --fasi-secondary: #2d1650;
                --fasi-accent: #7f5cf2;
                --fasi-background: #f4f3ff;
            }

            #MainMenu, header, footer {visibility: hidden;}
            [data-testid="stSidebar"] {display: none;}

            body {
                background: linear-gradient(180deg, rgba(42, 22, 80, 0.08), rgba(42, 22, 80, 0));
            }

            .fasitech-hero {
                background: linear-gradient(140deg, #1a0d2e 0%, #2d1650 45%, #4a1d7a 100%);
                border-radius: 24px;
                padding: 28px 36px;
                color: #ffffff;
                margin-bottom: 24px;
                box-shadow: 0 22px 45px rgba(42, 22, 80, 0.25);
            }

            .fasitech-hero h1 {
                font-size: 2.4rem;
                margin-bottom: 0.4rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
            }

            .fasitech-hero p {
                font-size: 1.05rem;
                opacity: 0.92;
            }

            .hero-badge {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                padding: 6px 16px;
                border-radius: 999px;
                background: rgba(255, 255, 255, 0.18);
                font-size: 0.85rem;
                letter-spacing: 0.03em;
                margin-bottom: 12px;
            }

            .status-band {
                background: #ffffff;
                border-radius: 18px;
                padding: 14px 22px;
                margin-bottom: 18px;
                display: flex;
                gap: 16px;
                justify-content: space-between;
                box-shadow: 0 12px 32px rgba(74, 29, 122, 0.08);
            }

            .status-pod {
                flex: 1 1 0;
            }

            .status-pod span {
                display: block;
                font-size: 0.78rem;
                text-transform: uppercase;
                letter-spacing: 0.06em;
                color: #5d5a76;
            }

            .status-pod strong {
                display: block;
                margin-top: 4px;
                font-size: 1.05rem;
                color: #2b2544;
            }

            .suggestion-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 12px;
                margin: 0 0 20px 0;
            }

            .stButton > button {
                border-radius: 18px;
                background: rgba(74, 29, 122, 0.12);
                color: #2d1650;
                border: 1px solid rgba(74, 29, 122, 0.2);
                padding: 12px 18px;
                font-weight: 600;
                transition: all 0.2s ease;
                text-align: left;
                box-shadow: none;
            }

            .stButton > button:hover {
                background: rgba(74, 29, 122, 0.22);
                border-color: rgba(74, 29, 122, 0.28);
            }

            .stButton > button:focus {
                outline: none;
                border-color: rgba(127, 92, 242, 0.8);
                box-shadow: 0 0 0 3px rgba(127, 92, 242, 0.25);
            }

            div[data-testid="stChatMessage"] {
                padding: 0.25rem 0;
            }

            .assistant-bubble, .user-bubble {
                border-radius: 20px;
                padding: 16px 20px;
                font-size: 1rem;
                line-height: 1.5;
                box-shadow: 0 10px 30px rgba(26, 13, 46, 0.08);
            }

            .assistant-bubble {
                background: #ffffff;
                border-left: 4px solid var(--fasi-accent);
                color: #2b2544;
            }

            .assistant-bubble.error {
                border-left-color: #e53e3e;
            }

            .user-bubble {
                background: linear-gradient(135deg, #6f5fe2 0%, #8a5cf7 100%);
                color: #ffffff;
            }

            .metrics-caption {
                font-size: 0.8rem;
                color: #6b6788;
            }

            .footer-note {
                text-align: center;
                color: #706a92;
                font-size: 0.85rem;
                margin-top: 28px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _init_session_state() -> None:
    """Garante os estados necessários para a página."""
    defaults: Dict[str, Any] = {
        "messages": [],
        "pending_question": None,
        "auto_submit": False,
        "last_question_time": datetime.fromtimestamp(0, tz=timezone.utc),
        "status_loaded": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if not st.session_state["messages"]:
        st.session_state["messages"].append(
            {
                "role": "assistant",
                "content": WELCOME_MESSAGE,
                "timestamp": datetime.now(timezone.utc),
                "success": True,
            }
        )


def _reset_conversation() -> None:
    """Limpa histórico local e remoto."""
    st.session_state["messages"] = [
        {
            "role": "assistant",
            "content": WELCOME_MESSAGE,
            "timestamp": datetime.now(timezone.utc),
            "success": True,
        }
    ]
    st.session_state["pending_question"] = None
    st.session_state["auto_submit"] = False
    st.session_state["last_question_time"] = datetime.fromtimestamp(0, tz=timezone.utc)

    try:
        _get_service().clear_conversation()
    except Exception:
        pass

    st.rerun()


# Renderização ----------------------------------------------------------------

def _render_header() -> None:
    """Renderiza hero banner e ações principais."""
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=160)

    st.markdown(
        """
        <div class="fasitech-hero">
            <div class="hero-badge">Diretoria Acadêmica • PPC</div>
            <h1>Diretor Virtual</h1>
            <p>
                Assistente inteligente para orientar estudantes e docentes sobre o Projeto
                Pedagógico do Curso de Sistemas de Informação.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    control_cols = st.columns([6, 2, 2])

    with control_cols[1]:
        with st.popover("ℹ️ Aviso de uso"):
            st.caption(
                "As respostas são geradas a partir do PPC oficial e podem conter imprecisões. "
                "Revise sempre as orientações acadêmicas antes de tomar decisões."
            )

    with control_cols[2]:
        st.button(
            "🔄 Reiniciar conversa",
            use_container_width=True,
            on_click=_reset_conversation,
        )


def _render_status_band() -> None:
    """Exibe métricas principais do serviço."""
    try:
        if not st.session_state.get("status_loaded"):
            with st.spinner("Inicializando assistente..."):
                status = _get_service().get_status()
            st.session_state["status_loaded"] = True
        else:
            status = _get_service().get_status()
    except Exception as exc:  # pragma: no cover - fluxo informativo
        st.warning(f"Não foi possível carregar o status do serviço: {exc}")
        return

    latency = status.get("last_latency")
    latency_text = f"{latency:.2f}s" if latency else "-"

    knowledge_label = "Carregada" if status.get("knowledge_loaded") else "Não carregada"

    st.markdown(
        f"""
        <div class="status-band">
            <div class="status-pod">
                <span>Modelo</span>
                <strong>{status.get('model_type') or 'Carregando...'}</strong>
            </div>
            <div class="status-pod">
                <span>Base PPC</span>
                <strong>{knowledge_label}</strong>
            </div>
            <div class="status-pod">
                <span>Perguntas respondidas</span>
                <strong>{status.get('total_questions', 0)}</strong>
            </div>
            <div class="status-pod">
                <span>Última latência</span>
                <strong>{latency_text}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_suggestions() -> None:
    """Mostra sugestões rápidas de perguntas."""
    st.markdown("#### Sugestões rápidas")
    with st.container():
        columns = st.columns(3)
        for index, item in enumerate(SUGGESTIONS):
            column = columns[index % len(columns)]
            with column:
                if st.button(item["label"], key=f"suggestion_{index}"):
                    st.session_state["pending_question"] = item["question"]
                    st.session_state["auto_submit"] = True
                    st.rerun()


def _render_history() -> None:
    """Mostra histórico de mensagens no formato de chat."""
    for message in st.session_state["messages"]:
        bubble_class = "user-bubble" if message["role"] == "user" else "assistant-bubble"
        if message["role"] == "assistant" and not message.get("success", True):
            bubble_class += " error"

        with st.chat_message(message["role"]):
            st.markdown(
                f'<div class="{bubble_class}">{message["content"]}</div>',
                unsafe_allow_html=True,
            )

            meta_parts = []
            timestamp = message.get("timestamp")
            if isinstance(timestamp, datetime):
                meta_parts.append(timestamp.strftime("%d/%m %H:%M"))
            if message.get("latency"):
                meta_parts.append(f"⏱️ {message['latency']:.2f}s")
            if meta_parts:
                st.caption(" • ".join(meta_parts))


def _consume_pending_question() -> Optional[str]:
    """Retorna a pergunta pendente gerada por botões de sugestão."""
    if st.session_state.get("auto_submit") and st.session_state.get("pending_question"):
        question = st.session_state["pending_question"]
        st.session_state["pending_question"] = None
        st.session_state["auto_submit"] = False
        return question
    return None


# Fluxo de perguntas ----------------------------------------------------------

def _handle_new_question(raw_question: str) -> None:
    """Processa a pergunta enviada pelo usuário."""
    question = (raw_question or "").strip()
    if not question:
        return

    timestamp = datetime.now(timezone.utc)
    st.session_state["messages"].append(
        {"role": "user", "content": question, "timestamp": timestamp}
    )

    with st.chat_message("user"):
        st.markdown(
            f'<div class="user-bubble">{question}</div>',
            unsafe_allow_html=True,
        )

    with st.chat_message("assistant"):
        with st.spinner("Consultando PPC e preparando a resposta..."):
            elapsed = datetime.now(timezone.utc) - st.session_state["last_question_time"]
            if elapsed < MIN_TIME_BETWEEN_REQUESTS:
                time.sleep((MIN_TIME_BETWEEN_REQUESTS - elapsed).total_seconds())

            st.session_state["last_question_time"] = datetime.now(timezone.utc)
            response = _get_service().ask_question(question)

        assistant_message: Dict[str, Any] = {
            "role": "assistant",
            "timestamp": datetime.now(timezone.utc),
        }

        if response.get("success"):
            answer_text = response.get("answer", "Resposta não disponível.")
            assistant_message.update(
                {
                    "content": answer_text,
                    "latency": response.get("latency"),
                    "success": True,
                }
            )
            st.markdown(
                f'<div class="assistant-bubble">{answer_text}</div>',
                unsafe_allow_html=True,
            )
            if response.get("latency"):
                st.caption(f"⏱️ {response['latency']:.2f}s")
        else:
            error_text = response.get("error", "Não foi possível responder agora.")
            assistant_message.update(
                {
                    "content": f"Desculpe, ocorreu um erro: {error_text}",
                    "success": False,
                }
            )
            st.markdown(
                f'<div class="assistant-bubble error">{error_text}</div>',
                unsafe_allow_html=True,
            )

        st.session_state["messages"].append(assistant_message)


# Função principal ------------------------------------------------------------

def main() -> None:
    st.set_page_config(
        page_title="Diretor Virtual - PPC",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    _inject_global_styles()
    _init_session_state()

    _render_header()
    _render_suggestions()

    _render_history()

    pending_question = _consume_pending_question()
    user_input = st.chat_input(
        "Digite aqui sua pergunta sobre o PPC...",
    )

    user_message = pending_question or user_input
    if user_message:
        _handle_new_question(user_message)

    # st.markdown(
    #     """
    #     <div class="footer-note">
    #         🤖 <strong>Diretor Virtual</strong> • Plataforma FasiTech • Projeto Pedagógico do Curso de Sistemas de Informação
    #     </div>
    #     """,
    #     unsafe_allow_html=True,
    # )


if __name__ == "__main__":
    main()
