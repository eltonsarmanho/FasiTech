"""
Página do Diretor Virtual - Chatbot sobre o PPC.
Interface inspirada em assistentes modernos, mantendo a identidade visual FasiTech.
"""

from __future__ import annotations

import streamlit as st
import sys
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import time

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.rag_ppc import ChatbotService, get_service

# Caminhos e identidade visual ------------------------------------------------
LOGO_PATH = PROJECT_ROOT / "src" / "resources" / "fasiOficial.png"

# Configuração da planilha de feedback (carrega de secrets.toml ou usa fallback)
try:
    FEEDBACK_SHEET_ID = st.secrets.get("AvalicaoDiretorVirtual", {}).get("sheet_id", "1HDGlJi9Uu2NX7MI0032BwGUWYpzSfNJAQWWsq4UJ07U")
except Exception:
    FEEDBACK_SHEET_ID = "1HDGlJi9Uu2NX7MI0032BwGUWYpzSfNJAQWWsq4UJ07U"

# Sugestões de perguntas rápidas
SUGGESTIONS = [
    {
        "label": "🎯 Disciplina Tutoria",
        "question": "Requisitos para disciplina de tutoria?",
    },
    {
        "label": "📚 Disciplinas iniciais",
        "question": "Quais são as atividades curriculares do 1° período do curso?",
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
        "label": "🧠 Artigos Científicos",
        "question": "Como funciona o acesso aos artigos científicos usando email institucional?",
    },
    {
        "label": "📑 TCC",
        "question": "Como funciona o Trabalho de Conclusão de Curso segundo o PPC?",
    },
]

MIN_TIME_BETWEEN_REQUESTS = timedelta(seconds=2)
WELCOME_MESSAGE = (
    "Olá! Eu sou o Diretor Virtual da FasiTech. Estou pronto para responder "
    "suas dúvidas sobre Curso de Sistemas de Informação."
)

fasi_service: Optional[ChatbotService] = None


# Utilitários -----------------------------------------------------------------

def _get_service() -> ChatbotService:
    """Retorna a instância singleton do serviço RAG."""
    global fasi_service
    if fasi_service is None:
        fasi_service = get_service()
    return fasi_service


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
    """Inicializa variáveis de sessão."""
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = str(uuid.uuid4())
        
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {
                "role": "assistant",
                "content": WELCOME_MESSAGE,
                "timestamp": datetime.now(timezone.utc),
                "success": True,
            }
        ]
    if "pending_question" not in st.session_state:
        st.session_state["pending_question"] = None
    if "auto_submit" not in st.session_state:
        st.session_state["auto_submit"] = False
    if "last_question_time" not in st.session_state:
        st.session_state["last_question_time"] = datetime.fromtimestamp(0, tz=timezone.utc)
    if "status_loaded" not in st.session_state:
        st.session_state["status_loaded"] = False


def _save_feedback_to_sheet(rating: int, pergunta: str = "", resposta: str = "") -> bool:
    """
    Salva o feedback do usuário na planilha do Google Sheets.
    
    Args:
        rating: Avaliação de 0 a 4 (retornado pelo st.feedback)
        pergunta: A pergunta feita pelo usuário
        resposta: A resposta dada pelo assistente
    
    Returns:
        True se salvou com sucesso, False caso contrário
    """
    try:
        from src.services.google_sheets import _get_credentials
        from googleapiclient.discovery import build
        
        # Converter rating de 0-4 para 1-5
        avaliacao = rating + 1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Preparar dados no formato correto (lista de valores)
        # Colunas: Data | Avaliação | Pergunta | Resposta
        values = [[timestamp, str(avaliacao), pergunta, resposta]]
        
        # Conectar à API do Google Sheets
        credentials = _get_credentials()
        service = build('sheets', 'v4', credentials=credentials)
        
        # Adicionar linha na planilha
        body = {'values': values}
        
        result = service.spreadsheets().values().append(
            spreadsheetId=FEEDBACK_SHEET_ID,
            range='Feedback!A:D',  # Colunas A até D da aba Feedback
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        
        return True
        
    except Exception as e:
        st.error(f"❌ Erro ao salvar feedback: {e}")
        import traceback
        st.error(f"Detalhes: {traceback.format_exc()}")
        return False


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
        _get_service().clear_conversation(session_id=st.session_state.get("session_id"))
        # Gerar novo ID de sessão ao reiniciar
        st.session_state["session_id"] = str(uuid.uuid4())
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
            <h1>Diretor Virtual</h1>
            <p>
                Assistente inteligente para orientar estudantes e docentes sobre o Projeto
                Pedagógico do Curso de Sistemas de Informação e outras dúvidas.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([5, 1])
    with col_right:
        st.button(
            "Reiniciar",
            use_container_width=True,
            on_click=_reset_conversation,
        )

    st.info(
        "ℹ️ As respostas são geradas a partir do PPC oficial (e outros documentos oficiais) e podem conter imprecisões. "
        "Revise sempre as orientações acadêmicas antes de tomar decisões."
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
    for idx, message in enumerate(st.session_state["messages"]):
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
            
            # Adicionar feedback apenas para respostas do assistente (exceto mensagem de boas-vindas)
            if message["role"] == "assistant" and message.get("success", True) and idx > 0:
                feedback_key = f"feedback_{idx}"
                feedback_saved_key = f"feedback_saved_{idx}"
                
                # Verificar se já foi salvo
                if feedback_saved_key not in st.session_state:
                    st.session_state[feedback_saved_key] = False
                
                # Se já foi salvo, mostrar apenas a confirmação
                if st.session_state[feedback_saved_key]:
                    st.success("✅ Feedback registrado com sucesso!")
                else:
                    # Renderizar componente de feedback
                    selected = st.feedback("stars", key=feedback_key)
                    
                    # Mostrar botão embaixo apenas se uma avaliação foi selecionada
                    if selected is not None:
                        if st.button("✅ Confirmar Avaliação", key=f"confirm_{idx}", type="primary", use_container_width=False):
                            # Buscar a pergunta anterior (mensagem do usuário)
                            pergunta = ""
                            if idx > 0 and st.session_state["messages"][idx - 1]["role"] == "user":
                                pergunta = st.session_state["messages"][idx - 1]["content"]
                            
                            resposta = message.get("content", "")
                            
                            if _save_feedback_to_sheet(selected, pergunta, resposta):
                                st.session_state[feedback_saved_key] = True
                                st.rerun()


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
            response = _get_service().ask_question(
                question, 
                session_id=st.session_state["session_id"]
            )

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
            
            # Adicionar o componente de feedback para nova resposta
            st.session_state["messages"].append(assistant_message)
            idx = len(st.session_state["messages"]) - 1
            feedback_key = f"feedback_{idx}"
            feedback_saved_key = f"feedback_saved_{idx}"
            
            # Inicializar estado
            if feedback_saved_key not in st.session_state:
                st.session_state[feedback_saved_key] = False
            
            # Renderizar componente de feedback
            selected = st.feedback("stars", key=feedback_key)
            
            # Mostrar botão embaixo apenas se uma avaliação foi selecionada
            if selected is not None:
                if st.button("✅ Confirmar Avaliação", key=f"confirm_{idx}", type="primary", use_container_width=False):
                    # A pergunta é a variável 'question' que já temos no contexto
                    # A resposta é a variável 'answer_text' que já temos
                    if _save_feedback_to_sheet(selected, question, answer_text):
                        st.session_state[feedback_saved_key] = True
                        st.success("✅ Feedback registrado com sucesso!")
                        st.rerun()
            
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
        page_title="Diretor Virtual",
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
        "Digite aqui sua pergunta sobre o curso de Sistemas de Informação...",
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
