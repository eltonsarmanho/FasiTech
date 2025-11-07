"""
Página do Diretor Virtual - Chatbot sobre PPC do curso.
Interface Streamlit para fazer perguntas sobre o Projeto Pedagógico do Curso.
"""

from __future__ import annotations
import streamlit as st
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import time

# Identidade visual
LOGO_PATH = Path(__file__).resolve().parents[2] / "resources" / "fasiOficial.png"

# Adicionar diretório raiz ao PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.services.rag_ppc import PPCChatbotService, get_ppc_service

# Serviço RAG gerenciado de forma preguiçosa
ppc_service: Optional[PPCChatbotService] = None


def _get_service():
    """Garante que o serviço esteja disponível."""
    global ppc_service
    if ppc_service is None:
        ppc_service = get_ppc_service()
    return ppc_service


def _render_custom_styles():
    """Aplica CSS customizado para o chatbot."""
    st.markdown(
        """
        <style>
            /* Ocultar menu padrão do Streamlit */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            
            /* Ocultar sidebar completamente */
            [data-testid="stSidebar"],
            section[data-testid="stSidebar"],
            [data-testid="collapsedControl"],
            [data-testid="stSidebarNav"] {
                display: none !important;
                visibility: hidden !important;
                width: 0 !important;
            }
            
            .main-header {
                background: linear-gradient(135deg, #1a0d2e 0%, #2d1650 50%, #4a1d7a 100%);
                border-radius: 20px;
                padding: 30px;
                margin-bottom: 30px;
                color: white;
                text-align: center;
                box-shadow: 0 10px 40px rgba(26, 13, 46, 0.3);
            }
            
            .main-header h1 {
                font-size: 2.2rem;
                font-weight: 700;
                margin-bottom: 10px;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }
            
            .main-header p {
                color: rgba(255, 255, 255, 0.9);
                font-size: 1.1rem;
                margin: 0;
            }
            
            /* Chat container */
            .chat-container {
                background: #f8fafc;
                border-radius: 15px;
                padding: 20px;
                margin: 20px 0;
                border: 1px solid #e2e8f0;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            
            /* User message */
            .user-message {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 20px;
                border-radius: 20px 20px 5px 20px;
                margin: 10px 0 10px 20%;
                box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
            }
            
            /* Bot message */
            .bot-message {
                background: white;
                color: #2d3748;
                padding: 15px 20px;
                border-radius: 20px 20px 20px 5px;
                margin: 10px 20% 10px 0;
                border-left: 4px solid #667eea;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            
            /* Status indicators */
            .status-success {
                background: #c6f6d5;
                color: #22543d;
                padding: 10px 15px;
                border-radius: 8px;
                border-left: 4px solid #38a169;
                margin: 10px 0;
            }
            
            .status-error {
                background: #fed7d7;
                color: #742a2a;
                padding: 10px 15px;
                border-radius: 8px;
                border-left: 4px solid #e53e3e;
                margin: 10px 0;
            }
            
            .status-info {
                background: #bee3f8;
                color: #2a69ac;
                padding: 10px 15px;
                border-radius: 8px;
                border-left: 4px solid #3182ce;
                margin: 10px 0;
            }
            
            /* Buttons */
            .stButton > button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                font-weight: 600;
                padding: 12px 24px;
                border-radius: 25px;
                transition: all 0.3s ease;
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.25);
            }
            
            .stButton > button:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
            }
            
            /* Text input */
            .stTextArea textarea {
                border-radius: 15px;
                border: 2px solid #e2e8f0;
                font-size: 1rem;
                padding: 15px;
                transition: border-color 0.3s ease;
            }
            
            .stTextArea textarea:focus {
                border-color: #667eea !important;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
            }
            
            /* Logo container */
            .logo-container {
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
                background: #ffffff;
                border-radius: 16px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
                margin-bottom: 20px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_header():
    """Renderiza o cabeçalho da página."""
    # Logo
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width='stretch')
    
    # Cabeçalho principal
    st.markdown(
        """
        <div class="main-header">
            <h1>🤖 Diretor Virtual</h1>
            <p>Assistente inteligente para consultas sobre o PPC do curso</p>
            <p><em>Faça perguntas sobre o Projeto Pedagógico, disciplinas, carga horária, objetivos e mais!</em></p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_service_status():
    """Renderiza o status do serviço."""
    with st.expander("🔧 Status do Serviço", expanded=False):
        try:
            status = _get_service().get_status()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🤖 Serviço:**")
                if status['initialized']:
                    st.markdown('<div class="status-success">✅ Inicializado</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="status-error">❌ Não inicializado</div>', unsafe_allow_html=True)
                
                st.markdown("**🧠 Modelo:**")
                model_type = status.get('model_type', 'Não carregado')
                if model_type != 'Não carregado':
                    st.markdown(f'<div class="status-success">✅ {model_type}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="status-error">❌ Modelo não carregado</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown("**📚 Base de Conhecimento:**")
                if status['knowledge_loaded']:
                    st.markdown('<div class="status-success">✅ PPC carregado</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="status-error">❌ PPC não carregado</div>', unsafe_allow_html=True)
                
                st.markdown("**📄 Arquivo PPC:**")
                if status['ppc_file_exists']:
                    st.markdown('<div class="status-success">✅ Arquivo encontrado</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="status-error">❌ Arquivo não encontrado</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.markdown(f'<div class="status-error">❌ Erro ao verificar status: {str(e)}</div>', unsafe_allow_html=True)


def _render_suggested_questions():
    """Renderiza sugestões de perguntas."""
    st.markdown("### 💡 Perguntas Sugeridas")
    
    suggestions = [
        "Qual é o objetivo do curso?",
        "Quantas horas de estágio são obrigatórias?",
        "Quais são as disciplinas do primeiro período?",
        "Como funciona o TCC?",
        "Qual a carga horária total do curso?",
        "Quais são os pré-requisitos das disciplinas?",
        "Como é a estrutura curricular?",
        "Quais são as competências que o curso desenvolve?"
    ]
    
    # Organizar em colunas
    cols = st.columns(2)
    
    for i, suggestion in enumerate(suggestions):
        col = cols[i % 2]
        with col:
            if st.button(
                suggestion,
                key=f"suggestion_{i}",
                help="Clique para usar esta pergunta"
            ):
                st.session_state.suggested_question = suggestion
                st.rerun()


def _render_chat_interface():
    """Renderiza a interface principal de chat."""
    # Inicializar histórico de chat se não existir
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Verificar se há pergunta sugerida
    suggested_question = st.session_state.get('suggested_question', '')
    if suggested_question:
        st.session_state.suggested_question = ''  # Limpar após usar
    
    # Container para o chat
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Mostrar histórico
    if st.session_state.chat_history:
        st.markdown("### 💬 Conversa")
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(
                    f'<div class="user-message"><strong>Você:</strong><br>{message["content"]}</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="bot-message"><strong>🤖 Diretor Virtual:</strong><br>{message["content"]}</div>',
                    unsafe_allow_html=True
                )
        
        # Botão para limpar conversa
        if st.button("🗑️ Limpar Conversa", help="Remove todo o histórico de conversa"):
            st.session_state.chat_history = []
            _get_service().clear_conversation()
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Campo de entrada
    st.markdown("### ❓ Sua Pergunta")
    
    question = st.text_area(
        "Digite sua pergunta sobre o PPC:",
        value=suggested_question,
        height=100,
        placeholder="Ex: Quantas disciplinas tem no curso? Qual a carga horária de estágio?",
        help="Faça perguntas específicas sobre o Projeto Pedagógico do Curso"
    )
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if st.button("🚀 Enviar Pergunta", disabled=not question.strip()):
            if question.strip():
                print("Pergunta enviada:", question)
                _process_question(question.strip())
            else:
                print("Nenhuma pergunta digitada.")
    
    with col2:
        if st.button("🎲 Pergunta Aleatória"):
            import random
            suggestions = [
                "Qual é o objetivo do curso?",
                "Quantas horas de estágio são obrigatórias?",
                "Quais são as disciplinas do primeiro período?",
                "Como funciona o TCC?",
                "Qual a carga horária total do curso?"
            ]
            


def _process_question(question: str):
    """Processa uma pergunta e exibe a resposta."""
    # Adicionar pergunta ao histórico
    st.session_state.chat_history.append({
        "role": "user",
        "content": question
    })
    
    # Mostrar indicador de carregamento
    with st.spinner("🤖 Processando sua pergunta..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Verificar status do serviço primeiro
            progress_bar.progress(10)
            status_text.text("Verificando status do serviço...")

            service_status = _get_service().get_status()
            if not service_status.get('initialized'):
                raise Exception("Serviço não inicializado")
            
            progress_bar.progress(30)
            status_text.text("Enviando pergunta para o modelo...")
            
            # Fazer pergunta ao serviço
            response = _get_service().ask_question(question)
            
            progress_bar.progress(80)
            status_text.text("Processando resposta...")
            
            if response:
                progress_bar.progress(100)
                status_text.text("Pergunta processada com sucesso!")
                
                # Adicionar resposta ao histórico
                answer = response
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer['answer']
                })
                
                # Mostrar método usado (para debug)
               
                st.success("✅ Pergunta processada com sucesso!")
                
            else:
                error_detail = response.get('error', 'Erro desconhecido')
                error_msg = f"❌ Erro ao processar pergunta: {error_detail}"
                st.error(error_msg)
                
                # Adicionar erro ao histórico
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"Desculpe, ocorreu um erro: {error_detail}"
                })
                
                # Sugerir uma pergunta mais simples
                st.info("💡 Tente uma pergunta mais específica, como: 'Qual é o nome do curso?' ou 'Quantas disciplinas tem o curso?'")
        
        except Exception as e:
            progress_bar.progress(100)
            status_text.text("Erro no processamento")
            
            error_msg = f"❌ Erro inesperado: {str(e)}"
            st.error(error_msg)
            
            # Adicionar erro ao histórico
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": f"Desculpe, ocorreu um erro técnico: {str(e)}"
            })
            
            # Mostrar informações de debug
            with st.expander("🔧 Informações de Debug"):
                st.text(f"Erro: {str(e)}")
                st.text(f"Status do serviço: {_get_service().get_status()}")
        
        finally:
            # Limpar elementos temporários
            progress_bar.empty()
            status_text.empty()
    
    # Recarregar página para mostrar nova resposta
    st.rerun()


def main():
    """Função principal da página."""
    # Iniciar rag service
    st.set_page_config(
        page_title="Diretor Virtual - PPC",
        layout="wide",
        page_icon="🤖",
        initial_sidebar_state="collapsed",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': None
        }
    )
    
    _render_custom_styles()
    _render_header()
    
    # Layout principal
    col1, col2 = st.columns([2, 1])
    
    with col1:
        _render_chat_interface()
    
    with col2:
        _render_service_status()
        st.markdown("---")
        _render_suggested_questions()
    
    # Rodapé
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #718096; font-size: 0.9rem; margin-top: 40px;">
            <p>🤖 <strong>Diretor Virtual</strong> - Assistente IA para consultas sobre o PPC</p>
            <p>Desenvolvido por <strong>Elton Sarmanho</strong> | Sistema FasiTech</p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
