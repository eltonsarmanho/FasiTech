from __future__ import annotations

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Iterable, Optional, List

# Carregar variáveis de ambiente
try:
    from backend.utils.env_loader import load_environment
    load_environment()
except ImportError:
    pass


def send_notification(subject: str, body: str, recipients: Iterable[str]) -> None:
    """
    Envia notificação por e-mail usando SMTP do Gmail.
    
    Args:
        subject: Assunto do e-mail
        body: Corpo do e-mail (texto)
        recipients: Lista de destinatários
    """
    send_email_with_attachments(subject, body, recipients, attachments=None)


def send_email_with_attachments(
    subject: str,
    body: str,
    recipients: Iterable[str],
    attachments: Optional[List] = None
) -> None:
    """
    Envia e-mail com anexos usando SMTP do Gmail.

    Args:
        subject: Assunto do e-mail
        body: Corpo do e-mail (texto)
        recipients: Lista de destinatários
        attachments: Lista de caminhos (str) ou tuplas (filename, bytes[, mimetype])
    """
    email_sender = os.getenv("EMAIL_SENDER", "fasicuntins@ufpa.br")
    email_password = os.getenv("EMAIL_PASSWORD")
    
    if not email_password:
        print("⚠️ Senha de e-mail não configurada. E-mail não será enviado.")
        print(f"   Configure EMAIL_PASSWORD no arquivo .env")
        return
    
    recipients_list = list(recipients)
    if not recipients_list:
        print("⚠️ Nenhum destinatário configurado. E-mail não será enviado.")
        return
    
    try:
        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = email_sender
        msg['To'] = ', '.join(recipients_list)
        msg['Subject'] = subject
        
        # Adicionar corpo do e-mail
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Adicionar anexos se fornecidos
        if attachments:
            for attachment in attachments:
                try:
                    if isinstance(attachment, (str, os.PathLike)):
                        # Caminho de arquivo
                        attachment_path = str(attachment)
                        if not os.path.exists(attachment_path):
                            continue
                        with open(attachment_path, 'rb') as f:
                            payload = f.read()
                        filename = os.path.basename(attachment_path)
                    elif isinstance(attachment, tuple):
                        # (filename, bytes) ou (filename, bytes, mimetype)
                        filename = attachment[0]
                        payload = attachment[1]
                    else:
                        continue

                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(payload)
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename=filename,
                    )
                    part.add_header('Content-Type', 'application/octet-stream', name=filename)
                    msg.attach(part)
                except Exception as e:
                    print(f"❌ Erro ao anexar arquivo: {str(e)}")
        
        # Conectar ao servidor SMTP do Gmail
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(email_sender, email_password)
            server.send_message(msg)
        
    # print(f"✅ E-mail enviado com sucesso para: {', '.join(recipients_list)}")
        
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {str(e)}")
        # Não lançar exceção para não bloquear o fluxo principal
        # O formulário deve continuar funcionando mesmo se o e-mail falhar
