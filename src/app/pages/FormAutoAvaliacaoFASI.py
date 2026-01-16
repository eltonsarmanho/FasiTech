# -*- coding: utf-8 -*-
"""
Formulário de Avaliação da Gestão da Faculdade de Sistemas de Informação.
Coleta feedback anônimo sobre transparência, comunicação, planejamento e suporte acadêmico.
"""
from __future__ import annotations

import streamlit as st
import datetime
import sys
from pathlib import Path
from typing import Any, Dict

# --- INÍCIO PADRÃO VISUAL INSTITUCIONAL ---
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.database.repository import save_avaliacao_gestao_submission

LOGO_PATH = Path(__file__).resolve().parents[2] / "resources" / "fasiOficial.png"

# Escalas de avaliação padronizadas
ESCALA_SATISFACAO = [
    "Muito insatisfeito",
    "Insatisfeito",
    "Neutro",
    "Satisfeito",
    "Muito satisfeito"
]

ESCALA_CONCORDANCIA = [
    "Discordo totalmente",
    "Discordo",
    "Neutro",
    "Concordo",
    "Concordo totalmente"
]


def _render_custom_styles():
    """Renderiza estilos customizados para o formulário de avaliação."""
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
            
            .avaliacao-hero {
                background: linear-gradient(135deg, #1a0d2e 0%, #2d1650 50%, #4a1d7a 100%);
                border-radius: 16px;
                padding: 36px;
                color: #ffffff;
                margin-bottom: 32px;
                box-shadow: 0 10px 30px rgba(26, 13, 46, 0.25);
                position: relative;
                overflow: hidden;
            }
            
            .avaliacao-hero::before {
                content: '';
                position: absolute;
                top: -30%;
                right: -5%;
                width: 300px;
                height: 300px;
                background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
                border-radius: 50%;
            }
            
            .avaliacao-hero h1 {
                font-size: 1.9rem;
                margin-bottom: 16px;
                font-weight: 700;
                text-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            
            .avaliacao-card {
                background: #ffffff;
                border-radius: 16px;
                padding: 36px;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
                border: 1px solid #e2e8f0;
                margin-bottom: 24px;
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
            
            .logo-container {
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 16px;
                background: #ffffff;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
                margin-bottom: 16px;
            }
            
            .form-section-title {
                color: #1a0d2e;
                font-size: 1.1rem;
                font-weight: 600;
                margin-bottom: 16px;
                margin-top: 24px;
                padding-bottom: 8px;
                border-bottom: 2px solid #7c3aed;
            }
            
            .question-label {
                color: #374151;
                font-size: 0.95rem;
                font-weight: 500;
                margin-bottom: 8px;
            }
            
            .info-box {
                background: #f0f9ff;
                border-left: 4px solid #0ea5e9;
                padding: 16px;
                border-radius: 8px;
                margin-bottom: 24px;
            }
            
            .info-box p {
                color: #0c4a6e;
                margin: 0;
                font-size: 0.9rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_periodo_atual():
    """Retorna o período acadêmico atual."""
    hoje = datetime.date.today()
    ano = hoje.year
    mes = hoje.month
    if 1 <= mes <= 6:
        return f"{ano}.(1 e 2)"
    else:
        return f"{ano}.(3 e 4)"


def render_form():
    """Renderiza o formulário de avaliação da gestão."""

    # Logo
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), use_container_width=True)

    # Hero section
    st.markdown(
        f"""
        <div class='avaliacao-hero'>
            <h1>📊 Formulário de Avaliação da Gestão</h1>
            <p style='font-size: 1.05rem; margin-bottom: 16px;'>
                Faculdade de Sistemas de Informação<br>
                <b>Período de referência: {get_periodo_atual()}</b>
            </p>
            <p style='font-size: 0.95rem; opacity: 0.9;'>
                Por favor, preencha este formulário de forma honesta. Seu feedback é fundamental 
                para melhorar a gestão da Faculdade de Sistemas de Informação.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Caixa de informação sobre anonimato
    st.markdown(
        """
        <div class='info-box'>
            <p>🔒 <strong>Todas as respostas são anônimas.</strong> Nenhuma informação pessoal será coletada ou vinculada às suas respostas.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Formulário principal
    with st.form("form_avaliacao_gestao"):
        
        # ============================================
        # SEÇÃO 1: Avaliação Geral da Gestão
        # ============================================
        st.markdown(
            '<div class="form-section-title">📋 Seção 1: Avaliação Geral da Gestão</div>',
            unsafe_allow_html=True
        )

        q1_transparencia = st.radio(
            "1. Como você avalia a transparência da gestão da Faculdade de Sistemas de Informação?",
            ESCALA_SATISFACAO,
            index=None,
            key="q1"
        )

        q2_comunicacao = st.radio(
            "2. Como você avalia a comunicação entre a gestão e os alunos/professores?",
            ESCALA_SATISFACAO,
            index=None,
            key="q2"
        )

        q3_acessibilidade = st.radio(
            "3. Como você avalia a acessibilidade da gestão para tratar de questões e preocupações?",
            ESCALA_SATISFACAO,
            index=None,
            key="q3"
        )

        q4_inclusao = st.radio(
            "4. A gestão da faculdade promove um ambiente acadêmico inclusivo e diversificado?",
            ESCALA_CONCORDANCIA,
            index=None,
            key="q4"
        )

        # ============================================
        # SEÇÃO 2: Planejamento e Organização
        # ============================================
        st.markdown(
            '<div class="form-section-title">📅 Seção 2: Planejamento e Organização</div>',
            unsafe_allow_html=True
        )

        q5_planejamento = st.radio(
            "5. Como você avalia o planejamento das atividades acadêmicas, incluindo a oferta de disciplinas e a alocação de professores?",
            ESCALA_SATISFACAO,
            index=None,
            key="q5"
        )

        q6_recursos = st.radio(
            "6. Como você avalia a gestão de recursos (infraestrutura, tecnologia, materiais) pela administração da faculdade?",
            ESCALA_SATISFACAO,
            index=None,
            key="q6"
        )

        q7_eficiencia = st.radio(
            "7. A gestão da faculdade é eficiente em resolver problemas administrativos e operacionais?",
            ESCALA_CONCORDANCIA,
            index=None,
            key="q7"
        )

        # ============================================
        # SEÇÃO 3: Suporte Acadêmico e Estudantil
        # ============================================
        st.markdown(
            '<div class="form-section-title">🎓 Seção 3: Suporte Acadêmico e Estudantil</div>',
            unsafe_allow_html=True
        )

        q8_suporte = st.radio(
            "8. Como você avalia o suporte acadêmico fornecido pela gestão, incluindo orientação acadêmica e apoio ao aluno?",
            ESCALA_SATISFACAO,
            index=None,
            key="q8"
        )

        q9_extracurricular = st.radio(
            "9. A gestão da faculdade promove atividades extracurriculares e de desenvolvimento profissional que atendem às necessidades dos alunos?",
            ESCALA_CONCORDANCIA,
            index=None,
            key="q9"
        )

        # ============================================
        # SEÇÃO 4: Sugestões e Comentários
        # ============================================
        st.markdown(
            '<div class="form-section-title">💬 Seção 4: Sugestões e Comentários</div>',
            unsafe_allow_html=True
        )

        q10_melhorias = st.text_area(
            "10. Que melhorias você sugeriria para a gestão da faculdade?",
            placeholder="Digite suas sugestões de melhoria aqui...",
            height=150,
            key="q10"
        )

        q11_outras_questoes = st.text_area(
            "11. Existem outras questões que você gostaria de destacar em relação à gestão da Faculdade de Sistemas de Informação?",
            placeholder="Digite outros comentários ou observações aqui...",
            height=150,
            key="q11"
        )

        # Botão de envio
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1])
	    
        with col1:
                submitted = st.form_submit_button("📤 Enviar Avaliação", width='stretch')      
		
        with col2:
             if st.form_submit_button("🏠 Voltar ao Menu Principal", width='stretch'):
                   st.switch_page("main.py")
        
        # Controle de estado para evitar duplo processamento
        if "avaliacao_processing" not in st.session_state:
            st.session_state.avaliacao_processing = False

        if submitted and not st.session_state.avaliacao_processing:
            st.session_state.avaliacao_processing = True
            
            # Validar campos obrigatórios (todas as perguntas de escala)
            campos_obrigatorios = [
                (q1_transparencia, "Pergunta 1 - Transparência"),
                (q2_comunicacao, "Pergunta 2 - Comunicação"),
                (q3_acessibilidade, "Pergunta 3 - Acessibilidade"),
                (q4_inclusao, "Pergunta 4 - Inclusão"),
                (q5_planejamento, "Pergunta 5 - Planejamento"),
                (q6_recursos, "Pergunta 6 - Recursos"),
                (q7_eficiencia, "Pergunta 7 - Eficiência"),
                (q8_suporte, "Pergunta 8 - Suporte"),
                (q9_extracurricular, "Pergunta 9 - Atividades Extracurriculares"),
            ]
            
            campos_vazios = [nome for valor, nome in campos_obrigatorios if valor is None]
            
            if campos_vazios:
                st.error(f"Por favor, responda todas as perguntas obrigatórias. Faltam: {', '.join(campos_vazios)}")
                st.session_state.avaliacao_processing = False
            else:
                import time
                with st.spinner("Aguarde, processando envio..."):
                    # Mapear respostas para valores numéricos (1-5)
                    def mapear_valor(resposta, escala):
                        if resposta in escala:
                            return escala.index(resposta) + 1
                        return ""
                    
                    row_data = {
                        "Periodo": get_periodo_atual(),
                        "Data/Hora": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Q1_Transparencia": q1_transparencia,
                        "Q1_Valor": mapear_valor(q1_transparencia, ESCALA_SATISFACAO),
                        "Q2_Comunicacao": q2_comunicacao,
                        "Q2_Valor": mapear_valor(q2_comunicacao, ESCALA_SATISFACAO),
                        "Q3_Acessibilidade": q3_acessibilidade,
                        "Q3_Valor": mapear_valor(q3_acessibilidade, ESCALA_SATISFACAO),
                        "Q4_Inclusao": q4_inclusao,
                        "Q4_Valor": mapear_valor(q4_inclusao, ESCALA_CONCORDANCIA),
                        "Q5_Planejamento": q5_planejamento,
                        "Q5_Valor": mapear_valor(q5_planejamento, ESCALA_SATISFACAO),
                        "Q6_Recursos": q6_recursos,
                        "Q6_Valor": mapear_valor(q6_recursos, ESCALA_SATISFACAO),
                        "Q7_Eficiencia": q7_eficiencia,
                        "Q7_Valor": mapear_valor(q7_eficiencia, ESCALA_CONCORDANCIA),
                        "Q8_Suporte": q8_suporte,
                        "Q8_Valor": mapear_valor(q8_suporte, ESCALA_SATISFACAO),
                        "Q9_Extracurricular": q9_extracurricular,
                        "Q9_Valor": mapear_valor(q9_extracurricular, ESCALA_CONCORDANCIA),
                        "Q10_Melhorias": q10_melhorias.strip() if q10_melhorias else "",
                        "Q11_Outras_Questoes": q11_outras_questoes.strip() if q11_outras_questoes else "",
                    }
                    
                    try:
                        save_avaliacao_gestao_submission(row_data)
                    except Exception as e:
                        st.error(f"Erro ao salvar no banco de dados: {e}")
                        st.session_state.avaliacao_processing = False
                        return
                
                # Mensagem de sucesso
                st.success("✅ Avaliação enviada com sucesso! Obrigado pelo seu feedback.")
                #st.balloons()
                st.session_state.avaliacao_processing = False
                time.sleep(st.secrets["sistema"]["timer"])
                st.switch_page("main.py")


def main():
    """Função principal do formulário."""
    st.set_page_config(
        page_title="Avaliação da Gestão - FASI",
        layout="centered",
        page_icon="📊",
        initial_sidebar_state="collapsed",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': None
        }
    )
    _render_custom_styles()
    render_form()


if __name__ == "__main__":
    main()
