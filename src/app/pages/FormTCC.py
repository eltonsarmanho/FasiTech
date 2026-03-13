from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

import streamlit as st

# Adicionar diretório raiz ao PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

LOGO_PATH = Path(__file__).resolve().parents[2] / "resources" / "fasiOficial.png"
# Aumentado para 50MB para acomodar documentos TCC (monografias, apresentações)
MAX_FILE_SIZE_MB = 50


def _normalize_professores(raw_value: Any) -> list[str]:
	"""Normaliza a lista de professores vinda do secrets.toml."""
	if raw_value is None:
		return []

	if isinstance(raw_value, (list, tuple)):
		return [str(item).strip() for item in raw_value if str(item).strip()]

	if isinstance(raw_value, str):
		return [item.strip() for item in raw_value.split(",") if item.strip()]

	return [str(raw_value).strip()] if str(raw_value).strip() else []


def _load_tcc_settings() -> dict[str, Any]:
	"""Carrega configurações TCC do secrets.toml."""
	try:
		return {
			"drive_folder_id": st.secrets["tcc"]["drive_folder_id"],
			"sheet_id": st.secrets["tcc"]["sheet_id"],
			"notification_recipients": st.secrets["tcc"].get("notification_recipients", []),
			"professores": _normalize_professores(st.secrets["tcc"].get("professores", [])),
		}
	except (KeyError, FileNotFoundError) as e:
		st.error(
			f"⚠️ Configurações TCC não encontradas em secrets.toml.\n\n"
			f"Por favor, configure a seção [tcc] com:\n"
			f"- drive_folder_id\n"
			f"- sheet_id\n"
			f"- notification_recipients\n"
			f"- professores"
		)
		raise ValueError("Configurações TCC ausentes") from e


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
			
			.tcc-hero {
				background: linear-gradient(135deg, #1a0d2e 0%, #2d1650 50%, #4a1d7a 100%);
				border-radius: 16px;
				padding: 36px;
				color: #ffffff;
				margin-bottom: 32px;
				box-shadow: 0 10px 30px rgba(26, 13, 46, 0.25);
				position: relative;
				overflow: hidden;
			}
			
			.tcc-hero::before {
				content: '';
				position: absolute;
				top: -30%;
				right: -5%;
				width: 300px;
				height: 300px;
				background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
				border-radius: 50%;
			}
			
			.tcc-hero h1 {
				font-size: 1.9rem;
				margin-bottom: 16px;
				font-weight: 700;
				text-shadow: 0 2px 4px rgba(0,0,0,0.2);
			}
			
			.tcc-card {
				background: #ffffff;
				border-radius: 16px;
				padding: 36px;
				box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
				border: 1px solid #e2e8f0;
				margin-bottom: 24px;
			}
			
			.tcc-instructions {
				font-size: 0.95rem;
				line-height: 1.7;
				margin-top: 12px;
				padding-left: 20px;
			}
			
			.tcc-instructions li {
				margin-bottom: 12px;
			}
			
			.tcc-instructions strong {
				color: #fbbf24;
				font-weight: 600;
			}
			
			.tcc-required {
				color: #ef4444;
				font-weight: 700;
			}
			
			.alert-box {
				background: #fef3c7;
				border-left: 4px solid #f59e0b;
				padding: 16px;
				margin: 20px 0;
				border-radius: 8px;
			}
			
			.alert-box h3 {
				color: #92400e;
				margin-bottom: 8px;
				font-size: 1.1rem;
			}
			
			.alert-box p, .alert-box ul {
				color: #78350f;
				margin: 8px 0;
			}
			
			.alert-box a {
				color: #7c3aed;
				font-weight: 600;
				text-decoration: underline;
			}
			
			.info-box {
				background: #dbeafe;
				border-left: 4px solid #3b82f6;
				padding: 16px;
				margin: 20px 0;
				border-radius: 8px;
			}
			
			.info-box h3 {
				color: #1e40af;
				margin-bottom: 8px;
				font-size: 1.1rem;
			}
			
			.info-box p, .info-box ol {
				color: #1e3a8a;
				margin: 8px 0;
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
		f"""
		<div class="tcc-hero">
			<h1>📚 Formulário de Submissão de TCC</h1>
			<p style="font-size: 1rem; margin-bottom: 16px;">Trabalho de Conclusão de Curso - TCC 1 e TCC 2</p>
			<ol class="tcc-instructions">
				<li>
					<strong>Leia atentamente</strong> as orientações abaixo antes de submeter seu TCC.
				</li>
				<li>
					Todos os campos são <strong>obrigatórios</strong>.
				</li>
				<li>
					Tamanho máximo por arquivo: <strong>{MAX_FILE_SIZE_MB} MB</strong>.
				</li>
			</ol>
		</div>
		""",
		unsafe_allow_html=True,
	)


def _validate_email(email: str) -> bool:
	"""Valida formato de email usando regex."""
	import re
	pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
	return re.match(pattern, email) is not None


def _validate_periodo(periodo: str) -> bool:
	"""Valida período no formato ANO.Numero (ex.: 2026.1)."""
	import re
	return bool(re.fullmatch(r"\d{4}\.[12]", periodo.strip()))


def _validate_submission(
	name: str,
	email: str,
	turma: str,
	polo: str,
	periodo: str,
	matricula: str,
	orientador: str,
	titulo: str,
	componente: str,
	uploaded_files: list[Any]
) -> list[str]:
	"""Executa validações básicas antes de enviar ao backend."""
	errors: list[str] = []
	
	# Nome obrigatório
	if not name.strip():
		errors.append("Nome completo é obrigatório.")
	
	# Email obrigatório e válido
	if not email.strip():
		errors.append("E-mail é obrigatório.")
	elif not _validate_email(email):
		errors.append("E-mail inválido. Use um formato válido (exemplo@ufpa.br).")
	
	# Turma obrigatória e deve ser ano no formato numérico
	if not turma.strip():
		errors.append("Turma é obrigatória.")
	elif not turma.strip().isdigit():
		errors.append("Turma deve ser um ano no formato numérico (ex: 2027, 2026).")
	elif len(turma.strip()) != 4:
		errors.append("Turma deve ter 4 dígitos (ex: 2027, 2026).")

	if not polo.strip():
		errors.append("Polo é obrigatório.")

	if not periodo.strip():
		errors.append("Período é obrigatório.")
	elif not _validate_periodo(periodo):
		errors.append("Período deve seguir o formato ANO.Numero (ex: 2026.1).")
	
	# Matrícula obrigatória
	if not matricula.strip():
		errors.append("Matrícula é obrigatória.")
	
	# Orientador obrigatório
	if not orientador.strip():
		errors.append("Nome do orientador é obrigatório.")
	
	# Título obrigatório
	if not titulo.strip():
		errors.append("Título do TCC é obrigatório.")
	
	# Componente curricular obrigatório
	if not componente:
		errors.append("Selecione o componente curricular (TCC 1 ou TCC 2).")
	
	# Validar anexos
	if not uploaded_files or len(uploaded_files) == 0:
		errors.append("Pelo menos um arquivo PDF deve ser anexado.")
	else:
		# Validar cada arquivo
		for idx, file in enumerate(uploaded_files, 1):
			if file.type not in {"application/pdf"}:
				errors.append(f"Arquivo {idx}: Apenas arquivos PDF são aceitos.")
			max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
			if file.size and file.size > max_bytes:
				errors.append(f"Arquivo {idx} ({file.name}): Excede o limite de {MAX_FILE_SIZE_MB} MB.")
		
		# Validação específica para TCC 2
		if componente == "TCC 2":
			if len(uploaded_files) < 3:
				errors.append(
					"TCC 2 requer no mínimo 3 arquivos: "
					"1) Declaração de Autoria, "
					"2) Termo de Autorização, "
					"3) TCC Final."
				)
	
	return errors


def render_form() -> None:
	_render_intro()
	tcc_settings = _load_tcc_settings()
	opcoes_orientadores = ["Selecione..."] + tcc_settings["professores"]
	
	
	# Componente curricular FORA do form para atualização dinâmica
	st.markdown("### Componente Curricular *")
	componente = st.radio(
		"Selecione o componente curricular:",
		options=["TCC 1", "TCC 2"],
		horizontal=True,
		label_visibility="collapsed",
		key="componente_radio"
	)
	
	# Orientações específicas por componente (atualiza dinamicamente)
	if componente == "TCC 1":
		st.info(
			"**📘 TCC 1 - Documentos Obrigatórios:**\n\n"
			"Anexe os seguintes arquivos:\n"
			"- 📄 ANEXO I das Diretrizes do TCC\n"
			"- 📄 ANEXO II das Diretrizes do TCC\n\n"
			"**Mínimo:** 2 arquivos PDF"
		)
	else:  # TCC 2
		st.warning(
			"**📗 TCC 2 - Documentos Obrigatórios:**\n\n"
			"⚠️ **ATENÇÃO:** Para TCC 2, você deve anexar **2 arquivos separados**:\n\n"
			"1. 📄 **Termo de Autorização** - [Baixar modelo](https://drive.google.com/file/d/1Gsev2C_Rhc-IuA_TP-MdHiWXE4m9kwtx/view?usp=sharing)\n"
			"2. 📄 **Versão Final do TCC**\n\n"
			"**Mínimo:** 2 arquivos PDF obrigatórios\n\n"
			"💡 **Importante:** A biblioteca (bibcameta@ufpa.br) receberá uma cópia da sua submissão."
		)
		
		# Estrutura Obrigatória do TCC - SOMENTE para TCC 2
		st.markdown(
			"""
			<div class="info-box">
				<h3>📋 Estrutura Obrigatória do TCC</h3>
				<p>Independentemente do formato do trabalho (memorial, artigo, relatório ou outro tipo de documento), é obrigatório incluir <strong>nessa ordem</strong>:</p>
				<ol>
					<li>Capa</li>
					<li>Contracapa</li>
					<li>
						Ficha Catalográfica<br>
						<a href="https://bcficat.ufpa.br/" target="_blank">
							🔗 Gerar Ficha Catalográfica
						</a>
					</li>
					<li>Folha de Assinatura da Banca (Obrigatório)</li>
				</ol>
				<p style="margin-top: 12px;"><strong>Certifique-se de seguir essas orientações para garantir a entrega correta do seu TCC.</strong></p>
			</div>
			""",
			unsafe_allow_html=True,
		)
	
	st.markdown("<br>", unsafe_allow_html=True)
	
	with st.form("formulario_tcc"):
		st.markdown("<span class='tcc-required'>*</span> Todos os campos são obrigatórios", unsafe_allow_html=True)
		st.markdown("<br>", unsafe_allow_html=True)
		
		# Campos do formulário
		col1, col2 = st.columns(2)
		
		name = col1.text_input("Nome Completo *", placeholder="Seu nome completo")
		email = col2.text_input("E-mail *", placeholder="seuemail@ufpa.br")
		turma = col1.text_input("Turma (Ano de Ingresso) *", placeholder="2027", max_chars=4)
		matricula = col2.text_input("Matrícula *", placeholder="202312345", max_chars=12)
		polo = col1.selectbox(
			"Polo *",
			options=["Selecione...", "CAMETÁ", "LIMOEIRO DO AJURU", "OEIRAS DO PARÁ"],
		)
		periodo = col2.text_input(
			"Período *",
			placeholder="2026.1",
			help="Informe o período em que você está matriculado no formato ANO.Numero (ex.: 2026.1).",
		)
		if periodo and not _validate_periodo(periodo):
			st.warning("Período inválido. Use o formato ANO.Numero (ex.: 2026.1).")
		st.caption("Informe o período em que você está matriculado. Exemplo: 2026.1")
		orientador = col1.selectbox(
			"Orientador(a) *",
			options=opcoes_orientadores,
			help="Selecione o professor orientador listado nas configurações do TCC.",
		)
		titulo = st.text_input("Título do TCC *", placeholder="Digite o título completo do seu TCC")
		
		st.markdown("<br>", unsafe_allow_html=True)
		
		# Upload de arquivos
		st.markdown("### Anexos (PDFs) *")
		
		# Mensagem de ajuda dinâmica
		help_text = (
			"TCC 1: Anexe ANEXO I e ANEXO II (mínimo 2 PDFs). "
			"TCC 2: Anexe Declaração de Autoria, Termo de Autorização e TCC Final (mínimo 3 PDFs)."
		)
		
		uploaded_files = st.file_uploader(
			f"Selecione os arquivos PDF (máximo {MAX_FILE_SIZE_MB} MB cada)",
			type=["pdf"],
			accept_multiple_files=True,
			help=help_text,
		)
		
		if uploaded_files:
			# Verificar se há arquivos que não são PDF e mostrar aviso imediato
			arquivos_invalidos = []
			arquivos_validos = []
			
			for file in uploaded_files:
				if file.type != "application/pdf":
					arquivos_invalidos.append(file.name)
				else:
					arquivos_validos.append(file)
			
			if arquivos_invalidos:
				st.error(
					f"⚠️ **Arquivo(s) não aceito(s):**\n\n"
					f"Os seguintes arquivos não são PDF e serão ignorados:\n"
					+ "\n".join(f"• {nome}" for nome in arquivos_invalidos)
					+ "\n\n**Apenas arquivos PDF são aceitos.**"
				)
			
			if arquivos_validos:
				st.success(f"✅ {len(arquivos_validos)} arquivo(s) PDF válido(s) selecionado(s)")
				for file in arquivos_validos:
					size_mb = file.size / (1024 * 1024)
					st.text(f"📄 {file.name} ({size_mb:.2f} MB)")
		
		st.markdown("<br>", unsafe_allow_html=True)
		
		# Botão de envio
		col1, col2 = st.columns([1, 1])
		with col1:
			submitted = st.form_submit_button("Enviar", width='stretch')
		with col2:
			if st.form_submit_button("🏠 Voltar ao Menu Principal", width='stretch'):
				st.switch_page("main.py")
		
		st.markdown('</div>', unsafe_allow_html=True)

		# Processar submissão
		if submitted:
			# Verificar se já está processando (evitar cliques múltiplos)
			if "tcc_processing" not in st.session_state:
				st.session_state.tcc_processing = False
			
			if not st.session_state.tcc_processing:
				# Marcar como processando
				st.session_state.tcc_processing = True
				
				errors = _validate_submission(
					name, email, turma, "" if polo == "Selecione..." else polo, periodo, matricula, "" if orientador == "Selecione..." else orientador, titulo, componente, uploaded_files or []
				)
				
				if errors:
					st.error("**Erros encontrados:**\n\n" + "\n".join(f"• {error}" for error in errors))
					st.session_state.tcc_processing = False  # Resetar flag em caso de erro
				else:
					status_placeholder = st.empty()
					status_placeholder.info("⏳ Processando dados da submissão. Aguarde...")
					with st.spinner("Processando submissão do TCC..."):
						try:
							# Preparar dados do formulário
							form_data = {
								"name": name,
								"registration": matricula,
								"email": email,
								"class_group": turma,
								"polo": "" if polo == "Selecione..." else polo,
								"periodo": periodo.strip(),
								"orientador": "" if orientador == "Selecione..." else orientador,
								"titulo": titulo,
								"componente": componente,
							}
							
							# Importar e processar submissão
							from src.services.form_service import process_tcc_submission
							
							result = process_tcc_submission(
								form_data=form_data,
								uploaded_files=uploaded_files,
								drive_folder_id=tcc_settings["drive_folder_id"],
								sheet_id=tcc_settings["sheet_id"],
								notification_recipients=tcc_settings["notification_recipients"],
							)
							
							st.success(
								f"✅ **TCC submetido com sucesso!**\n\n"
								f"**Resumo:**\n"
								f"- Nome: {name}\n"
								f"- Matrícula: {matricula}\n"
								f"- Componente: {componente}\n"
								f"- Orientador: {form_data['orientador']}\n"
								f"- Arquivos: {result['total_files']} documento(s)\n\n"
								f"Você receberá um e-mail de confirmação em breve."
							)
							status_placeholder.success("✅ Processamento concluído com sucesso.")
							st.info("🏠 Processo finalizado. Retornando ao menu principal...")
							
							# Resetar flag de processamento após sucesso
							st.session_state.tcc_processing = False
							time.sleep(2)
							st.switch_page("main.py")
							
						except Exception as e:
							status_placeholder.empty()
							st.error(f"❌ **Erro ao processar submissão:**\n\n{str(e)}")
							st.info("Por favor, tente novamente ou entre em contato com o suporte.")
							# Resetar flag de processamento em caso de erro
							st.session_state.tcc_processing = False
def main() -> None:
	st.set_page_config(
		page_title="Formulário TCC - FasiTech",
		layout="centered",
		page_icon="�",
		initial_sidebar_state="collapsed",
		menu_items={
			'Get Help': None,
			'Report a bug': None,
			'About': None
		}
	)
	render_form()


main()
