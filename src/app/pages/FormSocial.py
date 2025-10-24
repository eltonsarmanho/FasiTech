# -*- coding: utf-8 -*-
from timeit import main
import streamlit as st
import datetime

	# --- INÍCIO PADRÃO VISUAL INSTITUCIONAL ---
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.services.form_service import process_acc_submission

LOGO_PATH = Path(__file__).resolve().parents[2] / "resources" / "fasiOficial.png"
MAX_FILE_SIZE_MB = 10

def get_periodo_atual():
		import datetime
		hoje = datetime.date.today()
		ano = hoje.year
		mes = hoje.month
		if 1 <= mes <= 7:
			return f"{ano}.(1 e 2)"
		elif 8 <= mes <= 12:
			return f"{ano}.(3 e 4)"
def _render_custom_styles():
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
				.social-hero {
					background: linear-gradient(135deg, #1a0d2e 0%, #2d1650 50%, #4a1d7a 100%);
					border-radius: 16px;
					padding: 36px;
					color: #ffffff;
					margin-bottom: 32px;
					box-shadow: 0 10px 30px rgba(26, 13, 46, 0.25);
					position: relative;
					overflow: hidden;
				}
				.social-hero::before {
					content: '';
					position: absolute;
					top: -30%;
					right: -5%;
					width: 300px;
					height: 300px;
					background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
					border-radius: 50%;
				}
				.social-hero h1 {
					font-size: 1.9rem;
					margin-bottom: 16px;
					font-weight: 700;
					text-shadow: 0 2px 4px rgba(0,0,0,0.2);
				}
				.social-card {
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
					padding-bottom: 8px;
					border-bottom: 2px solid #7c3aed;
				}
			</style>
			""",
			unsafe_allow_html=True,
		)

def get_periodo_atual():
		import datetime
		hoje = datetime.date.today()
		ano = hoje.year
		mes = hoje.month
		if 1 <= mes <= 7:
			return f"{ano}.(1 e 2)"
		elif 8 <= mes <= 12:
			return f"{ano}.(3 e 4)"
		

def render_form():
		# Logo
		col_left, col_center, col_right = st.columns([1, 2, 1])
		with col_center:
			if LOGO_PATH.exists():
				st.markdown('<div class="logo-container">', unsafe_allow_html=True)
				st.image(str(LOGO_PATH), use_container_width=True)
				st.markdown('</div>', unsafe_allow_html=True)

		# Hero section
		st.markdown(
			f"""
			<div class='social-hero'>
				<h1>🤝 Formulário Social, Acadêmico e Saúde</h1>
				<p style='font-size: 1rem; margin-bottom: 16px;'>
					Questionário institucional para políticas de inclusão, diversidade, saúde mental e acompanhamento estudantil.<br>
					<b>Período de referência: {get_periodo_atual()}</b>
				</p>
				<ul style='font-size:0.98rem; margin-top:10px; padding-left:20px;'>
					<li>Preencha todos os campos com atenção.</li>
					<li>Os dados são confidenciais e utilizados apenas para fins institucionais.</li>
				</ul>
			</div>
			""",
			unsafe_allow_html=True,
		)

		with st.form("form_social"):
			st.markdown('<span style="color:#dc2626;font-weight:600;">*</span> Campo obrigatório', unsafe_allow_html=True)
			matricula = st.text_input("Matrícula *", max_chars=20)

			st.markdown('<div class="form-section-title">1. Perfil Pessoal (Inclusão e Diversidade)</div>', unsafe_allow_html=True)
			cor_etnia = st.radio(
				"Qual sua cor ou etnia/identidade racial?",
				[
					"Branco",
					"Preto",
					"Pardo",
					"Amarelo",
					"Indígena",
					"Quilombola",
					"Outra etnia",
					"Prefiro não responder"
				]
			)

			pcd = st.radio(
				"Você se considera Pessoa com Deficiência (PCD)?",
				["Sim", "Não", "Prefiro não responder"]
			)
			tipo_deficiencia = []
			if pcd == "Sim":
				tipo_deficiencia = st.multiselect(
					"Se 'Sim', qual o tipo de deficiência?",
					["Física", "Visual", "Auditiva", "Intelectual", "Múltipla", "Outra"]
				)

			st.markdown('<div class="form-section-title">2. Situação Socioeconômica</div>', unsafe_allow_html=True)
			renda = st.radio(
				f"Qual a renda familiar mensal total no período {get_periodo_atual()}?",
				[
					"Até 1 salário mínimo",
					"1 a 3 salários mínimos",
					"3 a 5 salários mínimos",
					"Acima de 5 a 10 salários mínimos",
					"Mais de 10 salários mínimos"
				]
			)

			st.markdown('<div class="form-section-title">3. Condições de Acesso e Deslocamento</div>', unsafe_allow_html=True)
			deslocamento = st.radio(
				f"Como você se desloca para a universidade no período {get_periodo_atual()}?",
				[
					"Transporte público (ônibus, trem, metrô, etc.)",
					"Transporte por aplicativo/táxi",
					"Carro/Moto próprio",
					"Carona/Fretado",
					"Bicicleta/A pé"
				]
			)

			st.markdown('<div class="form-section-title">4. Trabalho e Acadêmico</div>', unsafe_allow_html=True)
			trabalho = st.radio(
				f"Você trabalhava no período {get_periodo_atual()}?",
				[
					"Sim, estágio remunerado",
					"Sim, CLT/Concurso",
					"Sim, autônomo/informal",
					"Não"
				]
			)

			st.markdown('<div class="form-section-title">5. Saúde e Bem-Estar (Saúde Mental)</div>', unsafe_allow_html=True)
			saude_mental = st.radio(
				f"Em geral, como você avalia sua saúde mental no período {get_periodo_atual()}?",
				[
					"Muito boa",
					"Boa",
					"Regular",
					"Ruim",
					"Muito ruim",
					"Prefiro não responder"
				]
			)

			estresse = st.radio(
				f"Você sentiu ansiedade ou estresse elevado que interferiu nos seus estudos no período {get_periodo_atual()}?",
				[
					"Não",
					"Sim, ocasionalmente",
					"Sim, frequentemente",
					"Sim, a maior parte do tempo"
				]
			)

			acompanhamento = st.radio(
				"Você já buscou ou recebe acompanhamento psicológico/psiquiátrico?",
				[
					"Sim, atualmente",
					"Sim, no passado",
					"Nunca"
				]
			)

			st.markdown('<div class="form-section-title">6. Escolaridade dos Pais</div>', unsafe_allow_html=True)
			escolaridade_pai = st.selectbox(
				"Escolaridade do pai",
				[
					"Analfabeto",
					"Ensino Fundamental incompleto",
					"Ensino Fundamental completo",
					"Ensino Médio incompleto",
					"Ensino Médio completo",
					"Ensino Superior incompleto",
					"Ensino Superior completo",
					"Pós-graduação",
					"Não sei/Prefiro não responder"
				]
			)
			escolaridade_mae = st.selectbox(
				"Escolaridade da mãe",
				[
					"Analfabeto",
					"Ensino Fundamental incompleto",
					"Ensino Fundamental completo",
					"Ensino Médio incompleto",
					"Ensino Médio completo",
					"Ensino Superior incompleto",
					"Ensino Superior completo",
					"Pós-graduação",
					"Não sei/Prefiro não responder"
				]
			)

			st.markdown('<div class="form-section-title">7. Acesso à Internet e Moradia</div>', unsafe_allow_html=True)
			acesso_internet = st.radio(
				"Você possui acesso à internet em casa?",
				["Sim", "Não", "Às vezes", "Prefiro não responder"]
			)
			tipo_moradia = st.radio(
				"Tipo de moradia",
				[
					"Própria",
					"Alugada",
					"Cedida",
					"República/Estudantil",
					"Outra",
					"Prefiro não responder"
				]
			)

			submitted = st.form_submit_button("Salvar", use_container_width=True)
			st.markdown('</div>', unsafe_allow_html=True)

		if submitted:
			if not matricula.strip():
				st.error("Por favor, preencha o campo Matrícula.")
			else:
				st.success("Formulário enviado com sucesso! (Integração com Google Sheets e e-mail será implementada)")

def main():
		st.set_page_config(
			page_title="Formulário Social",
			layout="centered",
			page_icon="🤝",
			initial_sidebar_state="collapsed",
			menu_items={
				'Get Help': None,
				'Report a bug': None,
				'About': None
			}
		)
		_render_custom_styles()
		render_form()

			# Aqui: salvar no Google Sheets e enviar e-mail

main()

