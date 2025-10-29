from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict
import re

import streamlit as st

# Adicionar diretório raiz ao PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.services.form_service import process_acc_submission

LOGO_PATH = Path(__file__).resolve().parents[2] / "resources" / "fasiOficial.png"
# Aumentado para 50MB para evitar erro 413 no servidor
MAX_FILE_SIZE_MB = 50


def _load_acc_settings() -> Dict[str, Any]:
	"""Resgata configurações específicas do formulário via secrets/env."""
	try:
		acc_settings = st.secrets.get("acc", {}) if hasattr(st, "secrets") else {}
	except FileNotFoundError:
		# Arquivo secrets.toml não existe, usar valores padrão
		acc_settings = {}
	except Exception:
		# Qualquer outro erro ao carregar secrets
		acc_settings = {}
	
	recipients = acc_settings.get("notification_recipients", [])
	if isinstance(recipients, str):
		recipients = [email.strip() for email in recipients.split(",") if email.strip()]
	
	return {
		"drive_folder_id": acc_settings.get("drive_folder_id", ""),
		"sheet_id": acc_settings.get("sheet_id", ""),
		"notification_recipients": recipients,
	}


def _render_intro() -> None:
	st.markdown(
		"""
		<style>
			/* Estilos alinhados com identidade visual institucional */
			#MainMenu {visibility: hidden;}
			footer {visibility: hidden;}
			
			/* Ocultar sidebar completamente - aplicação imediata */
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
			
			.acc-hero {
				background: linear-gradient(135deg, #1a0d2e 0%, #2d1650 50%, #4a1d7a 100%);
				border-radius: 16px;
				padding: 36px;
				color: #ffffff;
				margin-bottom: 32px;
				box-shadow: 0 10px 30px rgba(26, 13, 46, 0.25);
				position: relative;
				overflow: hidden;
			}
			
			.acc-hero::before {
				content: '';
				position: absolute;
				top: -30%;
				right: -5%;
				width: 300px;
				height: 300px;
				background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
				border-radius: 50%;
			}
			
			.acc-hero h1 {
				font-size: 1.9rem;
				margin-bottom: 16px;
				font-weight: 700;
				text-shadow: 0 2px 4px rgba(0,0,0,0.2);
			}
			
			.acc-card {
				background: #ffffff;
				border-radius: 16px;
				padding: 36px;
				box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
				border: 1px solid #e2e8f0;
				margin-bottom: 24px;
			}
			
			.acc-instructions {
				font-size: 0.95rem;
				line-height: 1.7;
				margin-top: 12px;
				padding-left: 20px;
			}
			
			.acc-instructions li {
				margin-bottom: 12px;
			}
			
			.acc-instructions strong {
				color: #fbbf24;
				font-weight: 600;
			}
			
			.acc-required {
				color: #dc2626;
				font-weight: 600;
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

	# Logo
	col_left, col_center, col_right = st.columns([1, 2, 1])
	with col_center:
		if LOGO_PATH.exists():
			st.image(str(LOGO_PATH), width='stretch')
			st.markdown('</div>', unsafe_allow_html=True)
	
	# Hero section
	st.markdown(
		"""
		<div class="acc-hero">
			<h1>🎓 Formulário ACC</h1>
			<p style="font-size: 1rem; margin-bottom: 16px;">Atividades Complementares Curriculares</p>
			<ol class="acc-instructions">
				<li>
					Prezado(a) discente, antes de enviar seu arquivo, <strong>verifique se sua matrícula está ativa no SIGAA</strong>. Caso não esteja, entre em contato com a secretaria ou direção.
				</li>
				<li>
					O documento digital deve estar em <strong>formato PDF</strong> e conter <strong>todos os certificados consolidados em um único arquivo</strong>.
				</li>
				<li>
					Tamanho máximo: <strong>{MAX_FILE_SIZE_MB} MB</strong>. Arquivos maiores serão rejeitados.
				</li>
			</ol>
		</div>
		""",
		unsafe_allow_html=True,
	)


def _validate_turma(turma: str) -> bool:
    """Valida se a turma tem exatamente 4 dígitos numéricos."""
    return bool(re.match(r'^\d{4}$', turma))

def _validate_email(email: str) -> bool:
	"""Valida formato de email usando regex."""
	import re
	pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
	return re.match(pattern, email) is not None

def _validate_matricula(matricula: str) -> bool:
    """Valida se a matrícula possui exatamente 12 dígitos numéricos."""
    import re
    return bool(re.fullmatch(r"\d{12}", matricula))

def _validate_submission(name: str, registration: str, email: str, class_group: str, uploaded_file: Any) -> list[str]:
	"""Executa validações básicas antes de enviar ao backend."""
	errors: list[str] = []
	
	# Nome obrigatório
	if not name.strip():
		errors.append("Nome completo é obrigatório.")
	
	# Matrícula obrigatória
	if not registration.strip():
		errors.append("Matrícula é obrigatória.")
	
	# Email obrigatório e válido
	if not email.strip():
		errors.append("E-mail é obrigatório.")
	elif not _validate_email(email):
		errors.append("E-mail inválido. Use um formato válido (exemplo@ufpa.br).")
	
	# Turma obrigatória e deve ser ano no formato numérico (2024, 2025, etc)
	if not class_group.strip():
		errors.append("Turma é obrigatória.")
	elif not class_group.strip().isdigit():
		errors.append("Turma deve ser um ano no formato numérico (ex: 2027, 2026).")
	elif len(class_group.strip()) != 4:
		errors.append("Turma deve ter 4 dígitos (ex: 2027, 2026).")
	
	# Upload obrigatório
	if uploaded_file is None:
		errors.append("Anexo PDF é obrigatório.")
	else:
		if uploaded_file.type not in {"application/pdf"}:
			errors.append("Apenas arquivos PDF são aceitos.")
		
		# Validação de tamanho com informações detalhadas
		max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
		if uploaded_file.size:
			file_size_mb = uploaded_file.size / (1024 * 1024)
			if uploaded_file.size > max_bytes:
				errors.append(f"O arquivo ({file_size_mb:.1f} MB) excede o limite de {MAX_FILE_SIZE_MB} MB.")
			else:
				# Mostrar tamanho do arquivo para debug
				print(f"📄 Arquivo ACC válido: {uploaded_file.name} ({file_size_mb:.1f} MB)")
	
	return errors


def render_form() -> None:
	_render_intro()

	# Inicializar variáveis para evitar UnboundLocalError
	submitted = False
	name = registration = email = class_group = ""
	uploaded_file = None

	# Verificar se configurações foram carregadas
	config = _load_acc_settings()

	with st.form("formulario_acc"):
		st.markdown("<span class='acc-required'>*</span> Campo obrigatório", unsafe_allow_html=True)
		col1, col2 = st.columns(2)
		name = col1.text_input("Nome Completo *", placeholder="Seu nome completo")
		registration = col2.text_input("Matrícula *", placeholder="202312345", max_chars=12)
		
		if registration and not _validate_matricula(registration):
			st.warning("A matrícula deve conter exatamente 12 dígitos numéricos.")
		
		email = col1.text_input("E-mail *", placeholder="seuemail@ufpa.br")
		
		class_group = col2.text_input("Turma (Ano de Ingresso) *", placeholder="2027", max_chars=4)
		if class_group and not _validate_turma(class_group):
			st.warning("A turma deve conter exatamente 4 dígitos numéricos.")

		uploaded_file = st.file_uploader(
			"Anexo PDF *",
			type=["pdf"],
			accept_multiple_files=False,
			help="Arquivo PDF consolidado com todos os certificados (máximo 50 MB)",
		)
		submitted = st.form_submit_button("Enviar para análise", width='stretch')

		if not submitted:
			return

		# Verificar se já está processando (evitar cliques múltiplos)
		if "acc_processing" not in st.session_state:
			st.session_state.acc_processing = False
		
		if not st.session_state.acc_processing:
			# Marcar como processando apenas se não estiver processando
			st.session_state.acc_processing = True

			errors = _validate_submission(name, registration, email, class_group, uploaded_file)
			if errors:
				st.error("\n".join(f"• {error}" for error in errors))
				st.session_state.acc_processing = False  # Resetar em caso de erro
				return

			# Processar submissão RÁPIDA (sem IA)
			with st.spinner("📤 Enviando dados..."):
				try:
					# Chamar função de processamento rápido (sem IA)
					submission = process_acc_submission(
						{
							"name": name,
							"registration": registration,
							"email": email,
							"class_group": class_group,
						},
						uploaded_file,
						drive_folder_id=config["drive_folder_id"],
						sheet_id=config["sheet_id"],
						notification_recipients=config["notification_recipients"],
					)
				except ValueError as validation_error:
					st.error(str(validation_error))
					st.session_state.acc_processing = False  # Resetar em caso de erro
					return
				except Exception as unexpected:
					st.error("Não foi possível concluir o envio. Tente novamente em instantes.")
					st.exception(unexpected)
					st.session_state.acc_processing = False  # Resetar em caso de erro
					return

			# Mensagem de sucesso IMEDIATA
			st.success("✅ **Formulário ACC enviado com sucesso!**")
			st.info(
				"🤖 **Processamento com IA iniciado em background!**\n\n"
				"Seus certificados estão sendo processados por Inteligência Artificial. "
				"Você receberá um e-mail com a análise detalhada das cargas horárias assim que o processamento for concluído."
			)

			# Resetar flag de processamento
			st.session_state.acc_processing = False
			
			# Aguardar antes de redirecionar
			import time
			time.sleep(st.secrets["sistema"]["timer"])
			st.switch_page("main.py")


def main() -> None:
	st.set_page_config(
		page_title="Formulário ACC", 
		layout="centered", 
		page_icon="📝",
		initial_sidebar_state="collapsed",
		menu_items={
			'Get Help': None,
			'Report a bug': None,
			'About': None
		}
	)
	render_form()


main()
