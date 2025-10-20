#!/usr/bin/env python3
"""Script para configurar a aba 'Respostas TCC' na planilha do Google Sheets."""

import os
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

from src.utils.CredentialsEncoder import convertBase64ToJson

# Carregar variáveis de ambiente
load_dotenv()


def get_credentials():
    """Obtém as credenciais da service account."""
    credentials_base64 = os.getenv("GOOGLE_CLOUD_CREDENTIALS_FASI_BASE64")
    if not credentials_base64:
        raise ValueError("GOOGLE_CLOUD_CREDENTIALS_FASI_BASE64 não encontrado no .env")
    
    credentials_json = convertBase64ToJson(credentials_base64)
    
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
    ]
    
    credentials = service_account.Credentials.from_service_account_info(
        credentials_json, scopes=scopes
    )
    
    return credentials


def create_tcc_sheet_tab(sheet_id: str):
    """Cria a aba 'Respostas TCC' com cabeçalhos configurados."""
    credentials = get_credentials()
    service = build("sheets", "v4", credentials=credentials)
    
    # Nome da nova aba
    sheet_name = "Respostas TCC"
    
    # Verificar se a aba já existe
    spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    existing_sheets = [s['properties']['title'] for s in spreadsheet.get('sheets', [])]
    
    if sheet_name in existing_sheets:
        print(f"⚠️  Aba '{sheet_name}' já existe na planilha.")
        response = input("Deseja sobrescrever os cabeçalhos? (s/n): ")
        if response.lower() != 's':
            print("Operação cancelada.")
            return
    else:
        # Criar nova aba
        print(f"📄 Criando aba '{sheet_name}'...")
        request_body = {
            'requests': [{
                'addSheet': {
                    'properties': {
                        'title': sheet_name,
                        'gridProperties': {
                            'rowCount': 1000,
                            'columnCount': 10,
                            'frozenRowCount': 1,
                        }
                    }
                }
            }]
        }
        
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body=request_body
        ).execute()
        
        print(f"✅ Aba '{sheet_name}' criada com sucesso!")
    
    # Adicionar cabeçalhos
    print(f"📝 Configurando cabeçalhos na aba '{sheet_name}'...")
    
    headers = [
        "Timestamp",
        "Nome",
        "Matrícula",
        "Email",
        "Turma",
        "Componente",
        "Orientador",
        "Título",
        "Arquivos",
        "Quantidade de Anexos"
    ]
    
    range_name = f"{sheet_name}!A1:J1"
    body = {
        'values': [headers]
    }
    
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=range_name,
        valueInputOption='RAW',
        body=body
    ).execute()
    
    # Formatar cabeçalhos (negrito, fundo roxo, texto branco)
    sheet_id_number = None
    for sheet in spreadsheet.get('sheets', []):
        if sheet['properties']['title'] == sheet_name:
            sheet_id_number = sheet['properties']['sheetId']
            break
    
    if sheet_id_number is not None:
        print("🎨 Aplicando formatação aos cabeçalhos...")
        
        format_request = {
            'requests': [
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': sheet_id_number,
                            'startRowIndex': 0,
                            'endRowIndex': 1,
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'backgroundColor': {
                                    'red': 0.4863,
                                    'green': 0.2275,
                                    'blue': 0.9294
                                },
                                'textFormat': {
                                    'foregroundColor': {
                                        'red': 1.0,
                                        'green': 1.0,
                                        'blue': 1.0
                                    },
                                    'fontSize': 11,
                                    'bold': True
                                },
                                'horizontalAlignment': 'CENTER',
                                'verticalAlignment': 'MIDDLE'
                            }
                        },
                        'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)'
                    }
                },
                # Ajustar largura das colunas
                {
                    'updateDimensionProperties': {
                        'range': {
                            'sheetId': sheet_id_number,
                            'dimension': 'COLUMNS',
                            'startIndex': 0,
                            'endIndex': 1
                        },
                        'properties': {
                            'pixelSize': 180
                        },
                        'fields': 'pixelSize'
                    }
                },
                {
                    'updateDimensionProperties': {
                        'range': {
                            'sheetId': sheet_id_number,
                            'dimension': 'COLUMNS',
                            'startIndex': 1,
                            'endIndex': 8
                        },
                        'properties': {
                            'pixelSize': 200
                        },
                        'fields': 'pixelSize'
                    }
                },
                {
                    'updateDimensionProperties': {
                        'range': {
                            'sheetId': sheet_id_number,
                            'dimension': 'COLUMNS',
                            'startIndex': 8,
                            'endIndex': 9
                        },
                        'properties': {
                            'pixelSize': 400
                        },
                        'fields': 'pixelSize'
                    }
                }
            ]
        }
        
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body=format_request
        ).execute()
    
    print(f"✅ Aba '{sheet_name}' configurada com sucesso!")
    print(f"\n📊 Planilha: https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid={sheet_id_number}")
    print(f"\n✨ Cabeçalhos configurados:")
    for i, header in enumerate(headers, 1):
        print(f"   {i}. {header}")


def main():
    """Função principal."""
    print("=" * 60)
    print("🚀 Setup da Planilha TCC")
    print("=" * 60)
    print()
    
    # Solicitar ID da planilha
    print("Por favor, informe o ID da planilha do Google Sheets:")
    print("(Você pode encontrá-lo na URL da planilha)")
    print("Exemplo: https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit")
    print()
    
    sheet_id = input("Sheet ID: ").strip()
    
    if not sheet_id:
        print("❌ Sheet ID não pode estar vazio.")
        sys.exit(1)
    
    try:
        create_tcc_sheet_tab(sheet_id)
        print()
        print("=" * 60)
        print("✅ Configuração concluída com sucesso!")
        print("=" * 60)
        print()
        print("📝 Próximos passos:")
        print("   1. Verifique se a aba 'Respostas TCC' foi criada corretamente")
        print("   2. Atualize o .streamlit/secrets.toml com o sheet_id")
        print("   3. Teste o formulário TCC no Streamlit")
        
    except Exception as e:
        print(f"❌ Erro ao configurar planilha: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
