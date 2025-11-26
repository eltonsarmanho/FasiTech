#!/usr/bin/env python3
"""
Script para configurar a planilha de feedback do Diretor Virtual.
Cria a aba "Feedback" com as colunas necessárias se ainda não existir.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.google_sheets import get_sheet_tabs, append_rows
from googleapiclient.discovery import build
from src.services.google_sheets import _get_credentials

# ID da planilha de feedback (configurado em .streamlit/secrets.toml)
FEEDBACK_SHEET_ID = "1HDGlJi9Uu2NX7MI0032BwGUWYpzSfNJAQWWsq4UJ07U"


def create_feedback_sheet():
    """Cria a aba Feedback na planilha, se não existir."""
    try:
        credentials = _get_credentials()
        service = build('sheets', 'v4', credentials=credentials)
        
        # Verificar se a aba já existe
        existing_tabs = get_sheet_tabs(FEEDBACK_SHEET_ID)
        
        if "Feedback" in existing_tabs:
            print("✅ Aba 'Feedback' já existe!")
            return True
        
        # Criar nova aba
        request_body = {
            'requests': [{
                'addSheet': {
                    'properties': {
                        'title': 'Feedback',
                        'gridProperties': {
                            'rowCount': 1000,
                            'columnCount': 4  # Aumentado para 4 colunas
                        }
                    }
                }
            }]
        }
        
        service.spreadsheets().batchUpdate(
            spreadsheetId=FEEDBACK_SHEET_ID,
            body=request_body
        ).execute()
        
        print("✅ Aba 'Feedback' criada com sucesso!")
        
        # Adicionar cabeçalhos
        header_data = {
            'values': [['Data', 'Avaliação', 'Pergunta', 'Resposta']]
        }
        
        service.spreadsheets().values().update(
            spreadsheetId=FEEDBACK_SHEET_ID,
            range='Feedback!A1:D1',
            valueInputOption='RAW',
            body=header_data
        ).execute()
        
        print("✅ Cabeçalhos adicionados: 'Data', 'Avaliação', 'Pergunta' e 'Resposta'")
        
        # Formatar cabeçalho (negrito)
        format_request = {
            'requests': [{
                'repeatCell': {
                    'range': {
                        'sheetId': 0,  # Será ajustado automaticamente
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': 4  # Aumentado para 4 colunas
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {
                                'bold': True
                            }
                        }
                    },
                    'fields': 'userEnteredFormat.textFormat.bold'
                }
            }]
        }
        
        service.spreadsheets().batchUpdate(
            spreadsheetId=FEEDBACK_SHEET_ID,
            body=format_request
        ).execute()
        
        print("✅ Formatação aplicada!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar aba de feedback: {e}")
        return False


def verify_configuration():
    """Verifica se a configuração está correta."""
    print("\n🔍 Verificando configuração...")
    print(f"📋 Sheet ID: {FEEDBACK_SHEET_ID}")
    
    try:
        tabs = get_sheet_tabs(FEEDBACK_SHEET_ID)
        print(f"✅ Planilha acessível! Abas encontradas: {', '.join(tabs)}")
        
        if "Feedback" in tabs:
            print("✅ Aba 'Feedback' encontrada!")
            return True
        else:
            print("⚠️  Aba 'Feedback' não encontrada. Será criada...")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao acessar planilha: {e}")
        return False


def test_feedback_insertion():
    """Testa a inserção de um feedback de exemplo."""
    try:
        print("\n🧪 Testando inserção de feedback...")
        
        from datetime import datetime
        from googleapiclient.discovery import build
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pergunta = "Qual a carga horária do curso?"
        resposta = "O curso de Sistemas de Informação tem uma carga horária total de 3.060 horas."
        
        # Usar API diretamente para inserir os dados
        credentials = _get_credentials()
        service = build('sheets', 'v4', credentials=credentials)
        
        values = [[timestamp, "5", pergunta, resposta]]
        body = {'values': values}
        
        service.spreadsheets().values().append(
            spreadsheetId=FEEDBACK_SHEET_ID,
            range='Feedback!A:D',
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        
        print("✅ Feedback de teste inserido com sucesso!")
        print(f"   Data: {timestamp}")
        print(f"   Avaliação: 5 estrelas")
        print(f"   Pergunta: {pergunta}")
        print(f"   Resposta: {resposta[:60]}...")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao inserir feedback de teste: {e}")
        return False


def main():
    """Executa a configuração completa."""
    print("=" * 60)
    print("CONFIGURAÇÃO DA PLANILHA DE FEEDBACK - DIRETOR VIRTUAL")
    print("=" * 60)
    
    # Verificar configuração
    config_ok = verify_configuration()
    
    # Criar aba se necessário
    if not config_ok:
        if not create_feedback_sheet():
            print("\n❌ Falha na configuração. Verifique as permissões e tente novamente.")
            return
    
    # Testar inserção
    if test_feedback_insertion():
        print("\n" + "=" * 60)
        print("✅ CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 60)
        print("\n📝 Próximos passos:")
        print("1. Acesse a planilha em:")
        print(f"   https://docs.google.com/spreadsheets/d/{FEEDBACK_SHEET_ID}")
        print("2. Verifique se os dados de teste foram inseridos")
        print("3. O sistema de feedback está pronto para uso!")
    else:
        print("\n⚠️  Configuração parcialmente concluída.")
        print("   Verifique as permissões da conta de serviço.")


if __name__ == "__main__":
    main()
