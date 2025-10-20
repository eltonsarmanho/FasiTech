from __future__ import annotations

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Iterable

# Carregar variáveis de ambiente
try:
    from src.utils.env_loader import load_environment
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
        
        # Conectar ao servidor SMTP do Gmail
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(email_sender, email_password)
            server.send_message(msg)
        
        print(f"✅ E-mail enviado com sucesso para: {', '.join(recipients_list)}")
        
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {str(e)}")
        # Não lançar exceção para não bloquear o fluxo principal
        # O formulário deve continuar funcionando mesmo se o e-mail falhar
