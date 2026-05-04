from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

# Adicionar diretório raiz ao PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

LOGO_PATH = Path(__file__).resolve().parents[2] / "resources" / "fasiOficial.png"

# Listas de professores
PROFESSORES = [
    "Allan Barbosa Costa",
    "Elton Sarmanho Siqueira",
    "Carlos dos Santos Portela",
    "Fabricio de Souza Farias",
    "Ulisses Weyl da Cunha Costa",
    "Diovanni Moraes de Araujo",
    "Leonardo Nunes Gonçalves",
    "Keventon Rian Gimarães Gonçalves",
]

MEMBROS_BANCA = [
    "Allan Barbosa Costa",
    "Elton Sarmanho Siqueira",
    "Carlos dos Santos Portela",
    "Fabricio de Souza Farias",
    "Ulisses Weyl da Cunha Costa",
    "Diovanni Moraes de Araujo",
    "Leonardo Nunes Gonçalves",
    "Keventon Rian Gimarães Gonçalves",
]

# Mapeamento de professores para emails
PROFESSORES_EMAILS = {
    "Allan Barbosa Costa": "allanbcosta@ufpa.br",
    "Elton Sarmanho Siqueira": "eltonss@ufpa.br",
    "Carlos dos Santos Portela": "carlos.portela@ufpa.br",
    "Fabricio de Souza Farias": "fabricio.farias@ufpa.br",
    "Ulisses Weyl da Cunha Costa": "ulisses.costa@ufpa.br",
    "Diovanni Moraes de Araujo": "diovanni@ufpa.br",
    "Leonardo Nunes Gonçalves": "leonardo.goncalves@ufpa.br",
    "Keventon Rian Gimarães Gonçalves": "keventon@ufpa.br",
}

MODALIDADES = [
    "Monografia, podendo ser elaborada em coautoria (dupla)",
    "Texto científico na forma de artigo",
    "Publicação de trabalho em anais de evento técnico-científico, como primeiro autor, devendo ser defendido individualmente",
    "Memorial formativo, com a apresentação circunstanciada e fundamentada das vivências e experiências acadêmicas do(a) discente",
    "Publicação ou aceite de publicação de artigo em periódico científico, como primeiro autor, devendo ser defendido individualmente",
    "Submissão de artigo em periódico científico, como primeiro autor, devendo ser defendido individualmente",
    "Publicação de capítulo de livro com comitê editorial, como primeiro autor, devendo ser defendido individualmente",
    "Relatório de participação em projeto de ensino com plano de atividades concluído, na condição de bolsista ou voluntário(a)",
    "Relatório de participação em projeto de pesquisa com plano de iniciação científica concluído, na condição de bolsista ou voluntário(a)",
    "Relatório de participação em projeto de extensão com plano de trabalho concluído, na condição de bolsista ou voluntário(a)",
    "Relatório de experiência em estágio não obrigatório na área do curso",
    "Produção audiovisual",
    "Produção artística, cultural ou tecnológica",
    "Desenvolvimento de patentes, modelos de utilidade, cultivares ou marcas",
]


def _load_requerimento_settings() -> dict[str, Any]:
    """Carrega configurações do Requerimento TCC do secrets.toml."""
    try:
        return {
            "sheet_id": st.secrets["requerimento_tcc"]["sheet_id"],
            "notification_recipients": st.secrets["requerimento_tcc"].get("notification_recipients", []),
        }
    except (KeyError, FileNotFoundError) as e:
        st.error(
            f"⚠️ Configurações Requerimento TCC não encontradas em secrets.toml.\n\n"
            f"Por favor, configure a seção [requerimento_tcc] com:\n"
            f"- sheet_id\n"
            f"- notification_recipients"
        )
        raise ValueError("Configurações Requerimento TCC ausentes") from e


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
            
            .req-hero {
                background: linear-gradient(135deg, #1a0d2e 0%, #2d1650 50%, #4a1d7a 100%);
                border-radius: 16px;
                padding: 36px;
                color: #ffffff;
                margin-bottom: 32px;
                box-shadow: 0 10px 30px rgba(26, 13, 46, 0.25);
                position: relative;
                overflow: hidden;
            }
            
            .req-hero::before {
                content: '';
                position: absolute;
                top: -30%;
                right: -5%;
                width: 300px;
                height: 300px;
                background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
                border-radius: 50%;
            }
            
            .req-hero h1 {
                font-size: 1.9rem;
                margin-bottom: 16px;
                font-weight: 700;
                text-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            
            .req-card {
                background: #ffffff;
                border-radius: 16px;
                padding: 36px;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
                border: 1px solid #e2e8f0;
                margin-bottom: 24px;
            }
            
            .req-instructions {
                font-size: 0.95rem;
                line-height: 1.7;
                margin-top: 12px;
                padding-left: 20px;
            }
            
            .req-instructions li {
                margin-bottom: 12px;
            }
            
            .req-instructions strong {
                color: #fbbf24;
                font-weight: 600;
            }
            
            .req-required {
                color: #ef4444;
                font-weight: 700;
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
            
            .info-box p {
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
    
    # Hero section
    st.markdown(
        """
        <div class="req-hero">
            <h1>📝 Requerimento de TCC</h1>
            <p style="font-size: 1rem; margin-bottom: 16px;">Registro de informações para defesa do Trabalho de Conclusão de Curso</p>
            <ol class="req-instructions">
                <li>
                    <strong>Preencha todos os campos obrigatórios</strong> com atenção.
                </li>
                <li>
                    Para TCCs em <strong>dupla</strong>, ambos os alunos devem registrar as mesmas informações (título, resumo e palavras-chave).
                </li>
                <li>
                    Escolha uma data que esteja dentro do <strong>calendário da Jornada do TCC</strong>.
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


def _validate_submission(
    nome: str,
    matricula: str,
    email: str,
    titulo: str,
    resumo: str,
    palavras_chave: str,
    data_defesa: Any,
    modalidade: str,
    orientador: str,
    membro1: str,
    membro1_outro: str,
    membro2: str,
    membro2_outro: str,
    membro3: str = "",
    membro3_outro: str = "",
) -> list[str]:
    """Executa validações básicas antes de enviar ao backend."""
    errors: list[str] = []
    
    # Nome obrigatório
    if not nome.strip():
        errors.append("Nome completo é obrigatório.")
    
    # Matrícula obrigatória
    if not matricula.strip():
        errors.append("Matrícula é obrigatória.")
    
    # Email obrigatório e válido
    if not email.strip():
        errors.append("E-mail é obrigatório.")
    elif not _validate_email(email):
        errors.append("E-mail inválido. Use um formato válido (exemplo@ufpa.br).")
    
    # Título obrigatório
    if not titulo.strip():
        errors.append("Título do trabalho é obrigatório.")
    
    # Resumo obrigatório
    if not resumo.strip():
        errors.append("Resumo é obrigatório.")
    
    # Palavras-chave obrigatórias
    if not palavras_chave.strip():
        errors.append("Palavras-chave são obrigatórias.")
    
    # Data obrigatória
    if not data_defesa:
        errors.append("Data de defesa é obrigatória.")
    
    # Modalidade obrigatória
    if not modalidade:
        errors.append("Modalidade do trabalho é obrigatória.")
    
    # Orientador obrigatório (sem opção "Outro:")
    if not orientador or orientador == "":
        errors.append("Orientador é obrigatório.")
    
    # Membro 1 obrigatório - nova lógica
    if not membro1:
        errors.append("Membro 1 da Banca é obrigatório.")
    elif membro1 == "Outro" and not membro1_outro.strip():
        errors.append("Se selecionou 'Outro' para Membro 1, especifique o nome completo.")
    
    # Membro 2 obrigatório - nova lógica
    if not membro2:
        errors.append("Membro 2 da Banca é obrigatório.")
    elif membro2 == "Outro" and not membro2_outro.strip():
        errors.append("Se selecionou 'Outro' para Membro 2, especifique o nome completo.")
    
    # Membro 3 (opcional) - nova lógica
    if membro3 == "Outro" and not membro3_outro.strip():
        errors.append("Se selecionou 'Outro' para Membro 3, especifique o nome completo.")
    
    return errors


def _save_to_database(form_data: dict[str, Any]) -> int:
    """Salva os dados do requerimento no banco de dados."""
    from src.database.repository import save_requerimento_tcc_submission
    
    # Preparar dados para o banco
    db_data = {
        "nome_aluno": form_data["nome"],
        "matricula": form_data["matricula"],
        "email": form_data["email"],
        "telefone": form_data.get("telefone"),
        "turma": form_data.get("turma", ""),
        "orientador": form_data["orientador"],
        "coorientador": form_data.get("coorientador"),
        "titulo_trabalho": form_data["titulo"],
        "resumo": form_data["resumo"],
        "palavra_chave": form_data["palavras_chave"],
        "modalidade": form_data["modalidade"],
        "membro_banca1": form_data["membro1"],
        "membro_banca2": form_data["membro2"],
        "data_defesa": form_data.get("data_defesa"),
        "horario_defesa": form_data.get("horario_defesa"),
        "local_defesa": form_data.get("local_defesa"),
    }
    
    return save_requerimento_tcc_submission(db_data)


def _send_notification_email(form_data: dict[str, Any], recipients: list[str]) -> None:
    """Envia email de notificação sobre o requerimento."""
    from src.services.email_service import send_email_with_attachments
    
    # Montar lista de membros da banca
    membros = [form_data['membro1'], form_data['membro2']]
    if form_data.get('membro3'):
        membros.append(form_data['membro3'])
    membros_texto = ", ".join(membros)
    
    subject = "✅ Nova Resposta Registrada - Formulário Requisições de TCC"
    body = f"""\
Olá,

Uma nova resposta foi registrada no formulário requisições de TCC.

📅 Data da Defesa: {form_data['data_defesa']}
🎓 Nome: {form_data['nome']}
🔢 Matrícula: {form_data['matricula']}
� Orientador: {form_data['orientador']}
� Membros da Banca: {membros_texto}
📖 Título: {form_data['titulo']}
� Resumo: {form_data['resumo']}
🔑 Palavras-chave: {form_data['palavras_chave']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Sistema de Automação da FASI
"""
    
    # Montar lista de destinatários: aluno + orientador + faculdade (notification_recipients)
    all_recipients = recipients.copy()  # notification_recipients da faculdade
    
    # Adicionar email do aluno
    if form_data['email'] not in all_recipients:
        all_recipients.append(form_data['email'])
    
    # Adicionar email do orientador
    orientador_email = PROFESSORES_EMAILS.get(form_data['orientador'])
    if orientador_email and orientador_email not in all_recipients:
        all_recipients.append(orientador_email)
    
    send_email_with_attachments(subject, body, all_recipients)


def render_form() -> None:
    _render_intro()
    
    # Aviso importante no topo
    st.info("ℹ️ **Importante:** Todos os campos são obrigatórios (exceto Membro 3 da Banca)")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ============================================
    # FORMULÁRIO PRINCIPAL
    # ============================================
    with st.form("formulario_requerimento_tcc"):
        # Dados Pessoais
        st.markdown("### 👤 Dados Pessoais")
        col1, col2 = st.columns(2)
        
        nome = col1.text_input("Nome Completo *", placeholder="Seu nome completo")
        matricula = col2.text_input("Matrícula *", placeholder="202312345", max_chars=12)
        email = st.text_input("E-mail *", placeholder="seuemail@ufpa.br")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # ============================================
        # BANCA EXAMINADORA - AGORA DENTRO DO FORM
        # ============================================
        st.markdown("### 👥 Banca Examinadora")
        
        # Orientador (sem opção "Outro:")
        orientador = st.selectbox(
            "Orientador *",
            options=[""] + PROFESSORES,
            format_func=lambda x: "Selecione o orientador..." if x == "" else x,
            key="orientador_select"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Membro 1 da Banca
        membro1 = st.selectbox(
            "Membro 1 da Banca *",
            options=[""] + MEMBROS_BANCA + ["Outro"],
            format_func=lambda x: "Selecione o membro 1..." if x == "" else x,
            key="membro1_select"
        )
        
        membro1_outro = st.text_input(
            "Nome do Membro 1 (se selecionou Outro)", 
            placeholder="Digite o nome completo se selecionou 'Outro' acima",
            key="membro1_outro_input"
        )
        
        # Membro 2 da Banca
        membro2 = st.selectbox(
            "Membro 2 da Banca *",
            options=[""] + MEMBROS_BANCA + ["Outro"],
            format_func=lambda x: "Selecione o membro 2..." if x == "" else x,
            key="membro2_select"
        )
        
        membro2_outro = st.text_input(
            "Nome do Membro 2 (se selecionou Outro)", 
            placeholder="Digite o nome completo se selecionou 'Outro' acima",
            key="membro2_outro_input"
        )
        
        # Membro 3 da Banca (Opcional)
        membro3 = st.selectbox(
            "Membro 3 da Banca (Opcional)",
            options=["Nenhum"] + MEMBROS_BANCA + ["Outro"],
            key="membro3_select"
        )
        
        membro3_outro = st.text_input(
            "Nome do Membro 3 (se selecionou Outro)", 
            placeholder="Digite o nome completo se selecionou 'Outro' acima",
            key="membro3_outro_input"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Informações do Trabalho
        st.markdown("### 📚 Informações do Trabalho")
        
        titulo = st.text_input(
            "Título do trabalho *",
            placeholder="Digite o título completo do trabalho",
            help="⚠️ Caso o TCC for em DUPLA, registre o mesmo título no processo de requerimento"
        )
        
        resumo = st.text_area(
            "Resumo *",
            placeholder="Digite o resumo do trabalho",
            height=150,
            help="⚠️ Caso o TCC for em DUPLA, registre o mesmo resumo no processo de requerimento"
        )
        
        palavras_chave = st.text_input(
            "Palavras-chave *",
            placeholder="Palavra1, Palavra2, Palavra3",
            help="⚠️ Caso o TCC for em DUPLA, registre as mesmas palavras-chaves no processo de requerimento"
        )
        
        data_defesa = st.date_input(
            "Data da Defesa *",
            help="💡 Sugestão de data dentro do calendário da jornada do TCC",
            format="DD/MM/YYYY"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Modalidade do Trabalho
        st.markdown("### 📋 Modalidade do Trabalho")
        modalidade = st.selectbox(
            "Selecione a modalidade *",
            options=[""] + MODALIDADES,
            format_func=lambda x: "Selecione uma opção..." if x == "" else x
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Botão de envio
        col1, col2 = st.columns([1, 1])
        with col1:
            submitted = st.form_submit_button("Enviar Requerimento", width='stretch')

        with col2:
            if st.form_submit_button("🏠 Voltar ao Menu Principal", width='stretch'):
                st.switch_page("main.py")
        
        st.markdown('</div>', unsafe_allow_html=True)
        # Processar submissão
        if submitted:
            # Inicializar flag se não existir
            if "req_tcc_processing" not in st.session_state:
                st.session_state.req_tcc_processing = False
            
            # Processar apenas se não estiver processando (previne múltiplos cliques)
            if not st.session_state.req_tcc_processing:
                # Marcar como processando
                st.session_state.req_tcc_processing = True
                
                errors = _validate_submission(
                    nome, matricula, email, titulo, resumo, palavras_chave,
                    data_defesa, modalidade, orientador,
                    membro1, membro1_outro, membro2, membro2_outro,
                    membro3, membro3_outro
                )
                
                if errors:
                    st.error("**Erros encontrados:**\n\n" + "\n".join(f"• {error}" for error in errors))
                    st.session_state.req_tcc_processing = False  # Resetar flag
                else:
                    status_placeholder = st.empty()
                    status_placeholder.info("⏳ Processando dados da submissão. Aguarde...")
                    with st.spinner("Processando requerimento de TCC..."):
                        try:
                            # Carregar configurações
                            settings = _load_requerimento_settings()
                            
                            # Preparar dados (orientador não tem opção "Outro")
                            orientador_final = orientador
                            membro1_final = membro1_outro if membro1 == "Outro" else membro1
                            membro2_final = membro2_outro if membro2 == "Outro" else membro2
                            membro3_final = ""
                            if membro3 != "Nenhum":
                                membro3_final = membro3_outro if membro3 == "Outro" else membro3
                            
                            form_data = {
                                "nome": nome,
                                "matricula": matricula,
                                "email": email,
                                "titulo": titulo,
                                "resumo": resumo,
                                "palavras_chave": palavras_chave,
                                "data_defesa": data_defesa.strftime("%d/%m/%Y"),
                                "modalidade": modalidade,
                                "orientador": orientador_final,
                                "membro1": membro1_final,
                                "membro2": membro2_final,
                                "membro3": membro3_final,
                            }
                            
                            # Salvar no banco de dados
                            _save_to_database(form_data)
                            
                            # Enviar email
                            _send_notification_email(form_data, settings["notification_recipients"])
                            
                            st.success(
                                f"✅ **Requerimento de TCC enviado com sucesso!**\n\n"
                                f"**Resumo:**\n"
                                f"- Nome: {nome}\n"
                                f"- Matrícula: {matricula}\n"
                                f"- Título: {titulo}\n"
                                f"- Data da Defesa: {data_defesa.strftime('%d/%m/%Y')}\n"
                                f"- Orientador: {orientador_final}\n\n"
                                f"Você receberá um e-mail de confirmação em breve."
                            )
                            status_placeholder.success("✅ Processamento concluído com sucesso.")
                            st.info("🏠 Processo finalizado. Retornando ao menu principal...")
                            
                            # Resetar flag após sucesso
                            st.session_state.req_tcc_processing = False
                            time.sleep(st.secrets["sistema"]["timer"])
                            st.switch_page("main.py")
                            
                        except Exception as e:
                            status_placeholder.empty()
                            st.error(f"❌ **Erro ao processar requerimento:**\n\n{str(e)}")
                            st.info("Por favor, tente novamente ou entre em contato com o suporte.")
                            # Resetar flag em caso de erro
                            st.session_state.req_tcc_processing = False


def main() -> None:
    st.set_page_config(
        page_title="Requerimento TCC - FasiTech",
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
