from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

import streamlit as st

# Adicionar diretório raiz ao PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.services.form_service import process_acc_submission

LOGO_PATH = Path(__file__).resolve().parents[2] / "resources" / "fasiOficial.png"
MAX_FILE_SIZE_MB = 10


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
			st.markdown('<div class="logo-container">', unsafe_allow_html=True)
			st.image(str(LOGO_PATH), use_container_width=True)
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
					Tamanho máximo: <strong>10 MB</strong>. Arquivos maiores serão rejeitados.
				</li>
			</ol>
		</div>
		""",
		unsafe_allow_html=True,
	)


def _validate_submission(name: str, registration: str, email: str, class_group: str, uploaded_file: Any) -> list[str]:
	"""Executa validações básicas antes de enviar ao backend."""
	errors: list[str] = []
	if not name.strip():
		errors.append("Informe seu nome completo.")
	if not registration.strip():
		errors.append("Informe sua matrícula.")
	if not email.strip():
		errors.append("Informe seu e-mail institucional.")
	if not class_group.strip():
		errors.append("Informe sua turma.")
	if uploaded_file is None:
		errors.append("Anexe o comprovante único em PDF.")
	else:
		if uploaded_file.type not in {"application/pdf"}:
			errors.append("Envie apenas arquivos em PDF.")
		max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
		if uploaded_file.size and uploaded_file.size > max_bytes:
			errors.append("O arquivo excede o limite de 10 MB.")
	return errors


def render_form() -> None:
	_render_intro()
	
	# Verificar se configurações foram carregadas
	config = _load_acc_settings()
	if not config["drive_folder_id"] or not config["sheet_id"]:
		st.warning(
			"⚠️ **Configuração Incompleta**: O arquivo `.streamlit/secrets.toml` não está totalmente configurado. "
			"Os dados serão validados mas não serão enviados ao Google Drive/Sheets. "
			"Configure `drive_folder_id` e `sheet_id` para habilitar o envio completo."
		)
	
	st.markdown('<div class="acc-card">', unsafe_allow_html=True)
	with st.form("formulario_acc"):
		st.markdown("<span class='acc-required'>*</span> Campo obrigatório", unsafe_allow_html=True)
		col1, col2 = st.columns(2)
		name = col1.text_input("Nome *", placeholder="Seu nome completo")
		registration = col2.text_input("Matrícula *", placeholder="123456789")
		email = col1.text_input("Endereço de email *", placeholder="nome@fasitech.edu.br")
		class_group = col2.text_input("Turma *", placeholder="Curso / Período")

		uploaded_file = st.file_uploader(
			"Anexo (PDF único até 10 MB) *",
			type=["pdf"],
			accept_multiple_files=False,
			help="Faça upload de um arquivo PDF consolidado com todos os certificados.",
		)

		submit_placeholder = st.container()
		submitted = submit_placeholder.form_submit_button("Enviar para análise")

	st.markdown('</div>', unsafe_allow_html=True)

	if not submitted:
		return

	errors = _validate_submission(name, registration, email, class_group, uploaded_file)
	if errors:
		st.error("\n".join(f"• {error}" for error in errors))
		return

	with st.spinner("Enviando dados ao time de ACC..."):
		try:
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
			return
		except Exception as unexpected:
			st.error("Não foi possível concluir o envio. Tente novamente em instantes.")
			st.exception(unexpected)
			return

	st.success("Formulário ACC enviado com sucesso! Você receberá um e-mail quando o processamento for concluído.")
	st.toast("Envio realizado.")
	st.session_state.setdefault("last_acc_submission", submission.dict())


def main() -> None:
	st.set_page_config(page_title="Formulário ACC", layout="centered", page_icon="📝")
	render_form()


main()
