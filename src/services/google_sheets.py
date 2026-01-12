import pandas as pd
import os
from datetime import datetime
from typing import Any, Dict, Iterable
import logging

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from src.utils.retry import retry_with_backoff

# Carregar variáveis de ambiente
try:
    from src.utils.env_loader import load_environment
    load_environment()
except ImportError:
    pass

# Importar CredentialsEncoder
from src.utils.CredentialsEncoder import convertBase64ToJson
from src.services.google_drive import get_file_metadata

logger = logging.getLogger(__name__)

def get_sheet_tabs(sheet_id: str) -> list:
    """Retorna a lista de abas (sheets) de uma planilha Google."""
    # Verificar o tipo de arquivo primeiro
    try:
        file_metadata = get_file_metadata(sheet_id)
        mime_type = file_metadata.get("mimeType")

        if mime_type != "application/vnd.google-apps.spreadsheet":
            raise ValueError(
                f"O arquivo com ID '{sheet_id}' não é uma planilha Google nativa. "
                f"Seu formato é '{mime_type}'. Por favor, converta o arquivo para o formato Google Sheets."
            )
    except ValueError as e:
        # Adicionar contexto ao erro se a busca de metadados falhar
        raise ValueError(f"Erro ao verificar o arquivo no Google Drive: {e}")

    credentials = _get_credentials()
    service = build('sheets', 'v4', credentials=credentials)
    spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    return [sheet['properties']['title'] for sheet in spreadsheet['sheets']]
def read_sheet_tab(sheet_id: str, tab_name: str) -> pd.DataFrame:
    """Lê os dados de uma aba específica e retorna como DataFrame."""
    credentials = _get_credentials()
    service = build('sheets', 'v4', credentials=credentials)
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=tab_name
    ).execute()
    values = result.get('values', [])
    if not values:
        return pd.DataFrame()
    header, *rows = values
    return pd.DataFrame(rows, columns=header)
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
            # Verificar se é Projetos baseado nos campos presentes
            elif "Nome do Parecerista 1" in row:
                # Formato Projetos
                # Cabeçalhos: Carimbo de data/hora, Nome do Docente Responsável, Nome do Parecerista 1,
                #             Nome do Parecerista 2, Nome do Projeto, Carga Horária, Edital,
                #             Natureza, Ano do Edital, Solicitação, Anexos
                row_values = [
                    timestamp,                                      # Carimbo de data/hora
                    row.get("Nome do Docente Responsável", ""),    # Nome do Docente Responsável
                    row.get("Nome do Parecerista 1", ""),          # Nome do Parecerista 1
                    row.get("Nome do Parecerista 2", ""),          # Nome do Parecerista 2
                    row.get("Nome do Projeto", ""),                # Nome do Projeto
                    row.get("Carga Horária", ""),                  # Carga Horária
                    row.get("Edital", ""),                         # Edital
                    row.get("Natureza", ""),                       # Natureza
                    row.get("Ano do Edital", ""),                  # Ano do Edital
                    row.get("Solicitação", ""),                    # Solicitação
                    row.get("Anexos", ""),                         # Anexos
                ]
            # Verificar se é Plano de Ensino baseado nos campos presentes
            elif "Nome do Docente Responsável" in row:
                # Formato Plano de Ensino
                # Cabeçalhos: Carimbo de data/hora, Nome do Docente Responsável, Semestre, Anexos
                row_values = [
                    timestamp,                                      # Carimbo de data/hora
                    row.get("Nome do Docente Responsável", ""),    # Nome do Docente Responsável
                    row.get("Semestre", ""),                       # Semestre
                    row.get("Anexos", ""),                         # Anexos
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
            elif "Cor/Etnia" in row and "PCD" in row and "Tipo de Deficiência" in row:
                # Formato Social
                # Cabeçalhos: Matrícula, Periodo, Cor/Etnia, PCD, Tipo de Deficiência, Renda, Deslocamento, Trabalho, Saúde Mental, Estresse, Acompanhamento, Escolaridade Pai, Escolaridade Mãe, Qtd Computador, Qtd Celular, Computador Próprio, Gasto Internet, Acesso Internet, Tipo Moradia, Data/Hora
                row_values = [
                    row.get("Matrícula", ""),
                    row.get("Periodo", ""),
                    row.get("Cor/Etnia", ""),
                    row.get("PCD", ""),
                    row.get("Tipo de Deficiência", ""),
                    row.get("Renda", ""),
                    row.get("Deslocamento", ""),
                    row.get("Trabalho", ""),
                    row.get("Assistência Estudantil", ""),
                    row.get("Saúde Mental", ""),
                    row.get("Estresse", ""),
                    row.get("Acompanhamento", ""),
                    row.get("Escolaridade Pai", ""),
                    row.get("Escolaridade Mãe", ""),
                    row.get("Qtd Computador", ""),
                    row.get("Qtd Celular", ""),
                    row.get("Computador Próprio", ""),
                    row.get("Gasto Internet", ""),
                    row.get("Acesso Internet", ""),
                    row.get("Tipo Moradia", ""),
                    row.get("Data/Hora", timestamp),
                ]
            elif "Q1_Transparencia" in row and "Q2_Comunicacao" in row:
                # Formato Avaliação da Gestão FASI
                # Cabeçalhos: Periodo, Data/Hora, Q1-Q11 com respostas e valores numéricos
                row_values = [
                    row.get("Periodo", ""),
                    row.get("Data/Hora", timestamp),
                    row.get("Q1_Transparencia", ""),
                    row.get("Q1_Valor", ""),
                    row.get("Q2_Comunicacao", ""),
                    row.get("Q2_Valor", ""),
                    row.get("Q3_Acessibilidade", ""),
                    row.get("Q3_Valor", ""),
                    row.get("Q4_Inclusao", ""),
                    row.get("Q4_Valor", ""),
                    row.get("Q5_Planejamento", ""),
                    row.get("Q5_Valor", ""),
                    row.get("Q6_Recursos", ""),
                    row.get("Q6_Valor", ""),
                    row.get("Q7_Eficiencia", ""),
                    row.get("Q7_Valor", ""),
                    row.get("Q8_Suporte", ""),
                    row.get("Q8_Valor", ""),
                    row.get("Q9_Extracurricular", ""),
                    row.get("Q9_Valor", ""),
                    row.get("Q10_Melhorias", ""),
                    row.get("Q11_Outras_Questoes", ""),
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
        
    # print(f"✅ {result.get('updates').get('updatedRows')} linha(s) adicionada(s) à aba '{range_name}'")
        
    except Exception as e:
        print(f"❌ Erro ao escrever no Google Sheets: {str(e)}")
        raise

@retry_with_backoff(
    max_retries=3,
    base_delay=2.0,
    max_delay=30.0,
    retryable_status_codes=(500, 502, 503, 504),
)
def append_row_to_sheet(sheet_id: str, values: list, range_name: str = "Respostas ao formulário 1") -> dict:
    """
    Adiciona uma linha à planilha do Google Sheets.
    
    Implementa retry automático para erros temporários (503, 504, etc).
    
    Args:
        sheet_id: ID da planilha
        values: Lista de valores para adicionar
        range_name: Nome da aba/range
    
    Returns:
        Resposta da API do Google Sheets
    """
    if not sheet_id:
        raise ValueError("ID da planilha não fornecido")
    
    try:
        credentials = _get_credentials()
        service = build('sheets', 'v4', credentials=credentials)
        
        body = {
            'values': [values]
        }
        
        # Adicionar dados na planilha
        result = service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        
        logger.info(f"✅ Linha adicionada à aba '{range_name}': {values}")
        
        return result
    
    except Exception as e:
        logger.error(f"❌ Erro ao escrever no Google Sheets: {str(e)}")
        raise

