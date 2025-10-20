from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, Iterable

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Carregar variáveis de ambiente
try:
    from src.utils.env_loader import load_environment
    load_environment()
except ImportError:
    pass

# Importar CredentialsEncoder
from src.utils.CredentialsEncoder import convertBase64ToJson


def _get_credentials():
    """Carrega credenciais da conta de serviço do Google a partir do .env (base64)."""
    credentials_base64 = os.getenv("GOOGLE_CLOUD_CREDENTIALS_FASI_BASE64") or os.getenv("GOOGLE_CLOUD_CREDENTIALS_BASE64")
    
    if not credentials_base64:
        raise ValueError(
            "Credenciais do Google não encontradas. "
            "Defina GOOGLE_CLOUD_CREDENTIALS_BASE64 ou GOOGLE_CLOUD_CREDENTIALS_FASI_BASE64 no arquivo .env"
        )
    
    # Decodificar base64 para JSON usando CredentialsEncoder
    credentials_dict = convertBase64ToJson(credentials_base64)
    
    # Criar credenciais com os escopos necessários
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
    ]
    
    credentials = Credentials.from_service_account_info(
        credentials_dict, scopes=SCOPES
    )
    
    return credentials


def append_rows(rows: Iterable[Dict[str, Any]], sheet_id: str, range_name: str = "Respostas ao formulário 1") -> None:
    """
    Adiciona linhas em uma planilha do Google Sheets.
    
    Args:
        rows: Lista de dicionários com os dados a serem inseridos
        sheet_id: ID da planilha do Google Sheets
        range_name: Nome da aba/range (padrão: "Respostas ao formulário 1")
    """
    if not sheet_id:
        raise ValueError("ID da planilha não fornecido")
    
    try:
        credentials = _get_credentials()
        service = build('sheets', 'v4', credentials=credentials)
        
        # Converter dicionários em lista de valores
        values_to_append = []
        
        for row in rows:
            # Adicionar timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Montar linha com ordem específica para ACC
            row_values = [
                timestamp,
                row.get("Nome", ""),
                row.get("Matrícula", ""),
                row.get("Email", ""),
                row.get("Turma", ""),
                row.get("Arquivos", ""),
            ]
            
            values_to_append.append(row_values)
        
        body = {
            'values': values_to_append
        }
        
        # Adicionar dados na planilha
        result = service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        
        print(f"✅ {result.get('updates').get('updatedRows')} linha(s) adicionada(s) à planilha")
        
    except Exception as e:
        print(f"❌ Erro ao escrever no Google Sheets: {str(e)}")
        raise
