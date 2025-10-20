import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import datetime
import locale
from email.mime.base import MIMEBase
from email import encoders

# Importação condicional para evitar erro no AWS Lambda
try:
    from src.utils.PDFGenerator  import gerar_pdf_projetos, gerar_pdf_declaracao_projeto
    PDF_AVAILABLE = True
except ImportError as e:
    try:
        # Fallback para desenvolvimento local
        from src.utils.PDFGenerator import gerar_pdf_projetos, gerar_pdf_declaracao_projeto
        PDF_AVAILABLE = True
    except ImportError as e2:
        print(f"⚠️ PDFGenerator não disponível: {e} / {e2}")
        PDF_AVAILABLE = False

        def gerar_pdf_projetos(resposta):
            print("⚠️ PDF Generator não está disponível. PDF não será gerado.")
            return None

        def gerar_pdf_declaracao_projeto(resposta):
            print("⚠️ PDF Generator não está disponível. PDF de declaração não será gerado.")
            return None

# Carregar variáveis de ambiente do arquivo .env
load_dotenv(override=True)


# Configurações do servidor de e-mail
SMTP_SERVER = "smtp.gmail.com"  # Use "smtp.office365.com" para Outlook, etc.
SMTP_PORT = 587
EMAIL_SENDER = os.getenv("EMAIL_SENDER")  # Seu e-mail remetente
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # Senha do e-mail ou App Password


def formatar_data(data_iso):
    """Converte data do formato ISO 8601 para um formato mais legível."""
    try:

        locale.setlocale(locale.LC_TIME, "C")  # Alternativa para Linux
        # Converter a string para um objeto datetime
        dt = datetime.strptime(data_iso, "%Y-%m-%dT%H:%M:%S.%fZ")
        
        # Formatar para o estilo desejado: "20 de fevereiro de 2025, 14h42"
        data_formatada = dt.strftime("%d-%m-%Y %Hh%M")
        
        return data_formatada
    except ValueError:
        return "Data inválida"
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, "pt_BR")  # Tenta sem UTF-8
        except locale.Error:
            locale.setlocale(locale.LC_TIME, "C")  # Fallback para inglês padrão

def enviar_email_projetos(resposta):
    """Envia um e-mail notificando sobre uma nova submissão do formulário de Projetos."""
    
    # Criar lista de anexos formatados
    anexos = "\n".join(resposta[10:]) if len(resposta) > 9 else "Nenhum anexo enviado"
    body = f"""
    Olá,

    Uma nova submissão foi registrada no formulário de Projetos.

    🧑‍🏫 Docente: {resposta[1]}  
    📝 Parecerista 1: {resposta[2]}  
    📝 Parecerista 2: {resposta[3]}  
    📌 Projeto: {resposta[4]}  
    ⏳ Carga Horária: {resposta[5]} horas  
    📰 Edital: {resposta[6]}  
    🏷️ Natureza: {resposta[7]}  
    📆 Ano do Edital: {resposta[8]}  
    🏛️ Solicitação: {resposta[9]}  

    📎 Anexos: 
    {anexos}

    🔗 Você pode acessar os anexos através dos links fornecidos.
    🔎 Os pareceristas devem analisar artefatos e assinar o parecer.
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    🤖 Sistema de Automação da FASI
    """

    DESTINATARIOS = os.getenv("DESTINATARIOS", "").split(",")  # Lista de e-mails
    pareceristas_env = os.getenv("PARECERISTAS")
    pareceristas = dict(item.split(":") for item in pareceristas_env.split(","))
    email1 = pareceristas.get(resposta[2], "")
    email2 = pareceristas.get(resposta[3], "")
    DESTINATARIOS.append(email1)
    DESTINATARIOS.append(email2)

    caminhos_pdf = []
    if PDF_AVAILABLE:
        try:
            caminhos_pdf.append(gerar_pdf_projetos(resposta))
        except Exception as e:
            print(f"❌ Erro ao gerar PDF Parecer: {e}")
        
        # Gerar PDF de declaração apenas para projetos de Extensão
        if resposta[7].strip().lower() == "extensão":
            try:
                caminhos_pdf.append(gerar_pdf_declaracao_projeto(resposta))
            except Exception as e:
                print(f"❌ Erro ao gerar PDF Declaração: {e}")

    caminhos_pdf = [caminho for caminho in caminhos_pdf if caminho]

    enviar_email(
        body=body,
        nameForm='Projetos',
        DESTINATARIOS=DESTINATARIOS,
        caminhos_pdf=caminhos_pdf if caminhos_pdf else None,
    )

def enviar_email_plano_ensino(resposta):
    """Envia um e-mail notificando sobre uma nova submissão do formulário de Plano de Ensino."""

    # Criar lista de anexos formatados
    anexos = "\n".join(resposta[3:]) if len(resposta) > 2 else "Nenhum anexo enviado"
    body = f"""
    Olá,

    Uma nova submissão foi registrada no formulário de Plano de Ensino.

    🧑‍🏫 Docente: {resposta[1]}   
    📆 Semestre: {resposta[2]}  

    📎 Anexos: 
    {anexos}

    🔗 Você pode acessar os anexos através dos links fornecidos.
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    🤖 Sistema de Automação da FASI
    """

    DESTINATARIOS = os.getenv("DESTINATARIOS", "").split(",")  # Lista de e-mails
    pareceristas_env = os.getenv("PARECERISTAS")
    pareceristas = dict(item.split(":") for item in pareceristas_env.split(","))
    email1 = pareceristas.get(resposta[1], "")
    DESTINATARIOS.append(email1)

    
    enviar_email(body=body,nameForm='Plano de Ensino',DESTINATARIOS=DESTINATARIOS)

def enviar_email_acc(resposta):
    """Gera e envia e-mail formatado para notificações de ACC."""
    
    # Criar lista de anexos formatados
    anexos = "\n".join(resposta[5:]) if len(resposta) > 4 else "Nenhum anexo enviado"

    # Corpo do e-mail formatado corretamente
    body = f"""\
    Olá,

    Uma nova resposta foi registrada no formulário de Atividades Curriculares Complementares (ACC).

    📅 Data: {formatar_data(resposta[0])}
    🎓 Nome: {resposta[1]}
    🔢 Matrícula: {resposta[2]}
    📌 Turma: {resposta[4]}

    📎 Anexos: 
    {anexos}

    🔗 Você pode acessar os anexos através dos links fornecidos.

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    🤖 Sistema de Automação da FASI
    """
    DESTINATARIOS = os.getenv("DESTINATARIOS", "").split(",")  # Lista de e-mails

    enviar_email(body=body,nameForm='ACC',DESTINATARIOS=DESTINATARIOS)


def enviar_email_tcc(resposta):
    """Gera e envia e-mail formatado para notificações de TCC."""
    
    
    membros = resposta[7]+", "+resposta[8]+" e "+resposta[9] if len(resposta) > 12 else resposta[7]+" e "+resposta[8] 

    print(membros)
    # Corpo do e-mail formatado corretamente
    body = f"""\
    Olá,

    Uma nova resposta foi registrada no formulário requisições de TCC.

    📅 Data da Defesa: {formatar_data(resposta[12])}
    🎓 Nome: {resposta[1]}
    🔢 Matrícula: {resposta[2]}
    📌 Orientador: {resposta[6]}    
    👤 Membros da Banca: {membros}
    📖 Título: {resposta[4]}
    🔤 Resumo: {resposta[10]}   
    🔑 Palavras-chave: {resposta[11]}
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    🤖 Sistema de Automação da FASI
    """

    DESTINATARIOS = os.getenv("DESTINATARIOS", "").split(",")  # Lista de e-mails
    pareceristas_env = os.getenv("PARECERISTAS")
    pareceristas = dict(item.split(":") for item in pareceristas_env.split(","))
    orientador_email = pareceristas.get(resposta[6], "")
    aluno_email = resposta[3]
    DESTINATARIOS.append(orientador_email)
    DESTINATARIOS.append(aluno_email)

    enviar_email(body=body,nameForm='Requisição de Apresentação e Matrícula de TCC',DESTINATARIOS=DESTINATARIOS)


def enviar_email_tcc_documento(resposta):
    """Gera e envia e-mail formatado para notificações de TCC."""
    

    anexos = "\n".join(resposta[8:]) if len(resposta) > 7 else "Nenhum anexo enviado"
    # Corpo do e-mail formatado corretamente
    body = f"""\
    Olá,

    Uma nova resposta foi registrada no formulário de TCC.

    📅 Data: {formatar_data(resposta[0])}
    🎓 Nome: {resposta[1]}
    🔢 Matrícula: {resposta[4]}
    👤 Orientador: {resposta[5]}    
    📌 Título: {resposta[6]}
    📎 Anexos: 
    {anexos}

    🔗 Você pode acessar os anexos através dos links fornecidos.

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    🤖 Sistema de Automação da FASI
    """

    DESTINATARIOS = os.getenv("DESTINATARIOS", "").split(",")  # Lista de e-mails    
    aluno_email = resposta[2]
    if (resposta[7] == "TCC 2"):
        DESTINATARIOS.append("bibcameta@ufpa.br")
   
    DESTINATARIOS.append(aluno_email)

    enviar_email(body=body,nameForm=resposta[7],DESTINATARIOS=DESTINATARIOS)


def enviar_email_estagio(resposta):
    """Gera e envia e-mail formatado para notificações de Estágio."""
    

    anexos = "\n".join(resposta[8:]) if len(resposta) > 7 else "Nenhum anexo enviado"
    # Corpo do e-mail formatado corretamente
    body = f"""\
    Olá,

    Uma nova resposta foi registrada no formulário de Estágio.

    📅 Data: {formatar_data(resposta[0])}
    🎓 Nome: {resposta[1]}
    🔢 Matrícula: {resposta[4]}
    👤 Orientador: {resposta[5]}    
    📌 Título: {resposta[6]}
    📎 Anexos: 
    {anexos}

    🔗 Você pode acessar os anexos através dos links fornecidos.

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    🤖 Sistema de Automação da FASI
    """

    DESTINATARIOS = os.getenv("DESTINATARIOS", "").split(",")  # Lista de e-mails    
    aluno_email = resposta[2]
    DESTINATARIOS.append(aluno_email)

    enviar_email(body=body,nameForm=resposta[7],DESTINATARIOS=DESTINATARIOS)



def enviar_email(body,nameForm,DESTINATARIOS,caminhos_pdf=None):
    """Envia um e-mail notificando os destinatários sobre uma nova resposta."""
    try:
        # Verifica se as credenciais foram carregadas corretamente
        if not EMAIL_SENDER or not EMAIL_PASSWORD:
            raise ValueError("Credenciais de e-mail não carregadas corretamente! Verifique o arquivo .env.")

        # Configuração do e-mail
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = ", ".join(DESTINATARIOS)
        msg["Subject"] = f"📥 Nova Resposta Recebida no Formulário de {nameForm}"

        # Corpo do e-mail
        
        msg.attach(MIMEText(body, "plain"))

        # Anexar os PDFs gerados
        pdf_paths = []
        if isinstance(caminhos_pdf, (list, tuple, set)):
            pdf_paths = [caminho for caminho in caminhos_pdf if caminho]
        elif caminhos_pdf:
            pdf_paths = [caminhos_pdf]

        for caminho_pdf in pdf_paths:
            with open(caminho_pdf, "rb") as pdf_file:
                part = MIMEBase("application", "pdf")
                part.set_payload(pdf_file.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename*=UTF-8''{os.path.basename(caminho_pdf)}",
                )
                msg.attach(part)

        # Conectar ao servidor SMTP e enviar o e-mail
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, DESTINATARIOS, msg.as_string())
        server.quit()

        print("📧 E-mail enviado com sucesso!")

        

    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")


