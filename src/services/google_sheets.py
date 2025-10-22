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
        range_name: Nome da aba/range (padrão: "Respostas ao formulário 1" para ACC, "Respostas TCC" para TCC)
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
            
            # Verificar se é Requerimento TCC baseado nos campos presentes
            if "Título do trabalho" in row:
                # Formato Requerimento TCC
                # Cabeçalhos: Carimbo de data/hora, Nome, Matrícula, Email, Título do trabalho,
                #             Modalidade do Trabalho, Orientador, Membro 1 da Banca, Membro 2 da Banca,
                #             Membro 3 da Banca (Opcional), Resumo, Palavras-chave, Data
                row_values = [
                    timestamp,                                      # Carimbo de data/hora
                    row.get("Nome", ""),                           # Nome
                    row.get("Matrícula", ""),                      # Matrícula
                    row.get("Email", ""),                          # Email
                    row.get("Título do trabalho", ""),             # Título do trabalho
                    row.get("Modalidade do Trabalho", ""),         # Modalidade do Trabalho
                    row.get("Orientador", ""),                     # Orientador
                    row.get("Membro 1 da Banca", ""),              # Membro 1 da Banca
                    row.get("Membro 2 da Banca", ""),              # Membro 2 da Banca
                    row.get("Membro 3 da Banca (Opcional)", ""),   # Membro 3 da Banca (Opcional)
                    row.get("Resumo", ""),                         # Resumo
                    row.get("Palavras-chave", ""),                 # Palavras-chave
                    row.get("Data", ""),                           # Data
                ]
            # Verificar se é Estágio baseado nos campos presentes
            elif "Orientador ou Supervisor" in row:
                # Formato Estágio
                # Cabeçalhos: Carimbo de data/hora, Nome do Aluno, Email, Turma, Matrícula,
                #             Orientador ou Supervisor, Título, Componente Curricular, Anexos
                row_values = [
                    timestamp,                                      # Carimbo de data/hora
                    row.get("Nome do Aluno", ""),                  # Nome do Aluno
                    row.get("Email", ""),                          # Email
                    row.get("Turma", ""),                          # Turma
                    row.get("Matrícula", ""),                      # Matrícula
                    row.get("Orientador ou Supervisor", ""),       # Orientador ou Supervisor
                    row.get("Título", ""),                         # Título
                    row.get("Componente Curricular", ""),          # Componente Curricular
                    row.get("Anexos", ""),                         # Anexos
                ]
            # Verificar se é TCC baseado nos campos presentes
            elif "Componente" in row:
                # Formato TCC - mapeado para os cabeçalhos da planilha existente
                # Cabeçalhos: Carimbo de data/hora, Nome do aluno, Email, Turma, Matrícula, 
                #             Orientador, Título do TCC, Componente Curricular, Anexos
                row_values = [
                    timestamp,                          # Carimbo de data/hora
                    row.get("Nome", "").upper(),        # Nome do aluno (Em maiúscula)
                    row.get("Email", ""),               # Email
                    row.get("Turma", ""),               # Turma
                    row.get("Matrícula", ""),           # Matrícula
                    row.get("Orientador", ""),          # Orientador
                    row.get("Título", ""),              # Título do TCC
                    row.get("Componente", ""),          # Componente Curricular
                    row.get("Arquivos", ""),            # Anexos
                ]
            else:
                # Formato ACC
                row_values = [
                    timestamp,
                    row.get("Nome", ""),
                    row.get("Matrícula", ""),
                    row.get("Email", ""),
                    row.get("Turma", ""),
                    row.get("Arquivos", ""),
                ]
                
                # Adicionar carga horária se disponível
                if "Carga Horária" in row:
                    row_values.append(row.get("Carga Horária", ""))
            
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
        
        print(f"✅ {result.get('updates').get('updatedRows')} linha(s) adicionada(s) à aba '{range_name}'")
        
    except Exception as e:
        print(f"❌ Erro ao escrever no Google Sheets: {str(e)}")
        raise
