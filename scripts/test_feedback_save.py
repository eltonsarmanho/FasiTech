#!/usr/bin/env python3
"""
Script de teste para verificar o salvamento de feedback na planilha.
"""

import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Configuração
FEEDBACK_SHEET_ID = "1HDGlJi9Uu2NX7MI0032BwGUWYpzSfNJAQWWsq4UJ07U"

def test_feedback_save():
    """Testa o salvamento de feedback diretamente."""
    print("=" * 60)
    print("TESTE DE SALVAMENTO DE FEEDBACK")
    print("=" * 60)
    
    try:
        from src.services.google_sheets import _get_credentials
        from googleapiclient.discovery import build
        
        print("\n✅ Imports OK")
        
        # Conectar à API
        print("🔑 Obtendo credenciais...")
        credentials = _get_credentials()
        print("✅ Credenciais obtidas")
        
        print("🔗 Conectando ao Google Sheets...")
        service = build('sheets', 'v4', credentials=credentials)
        print("✅ Conexão estabelecida")
        
        # Preparar dados de teste
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        avaliacao = "5"  # Teste com 5 estrelas
        pergunta = "Qual a carga horária do curso?"
        resposta = "O curso de Sistemas de Informação tem uma carga horária total de 3.060 horas."
        values = [[timestamp, avaliacao, pergunta, resposta]]
        
        print(f"\n📝 Dados de teste:")
        print(f"   Data: {timestamp}")
        print(f"   Avaliação: {avaliacao} estrelas")
        print(f"   Pergunta: {pergunta}")
        print(f"   Resposta: {resposta[:60]}...")
        
        # Tentar salvar
        print(f"\n💾 Salvando na planilha {FEEDBACK_SHEET_ID}...")
        body = {'values': values}
        
        result = service.spreadsheets().values().append(
            spreadsheetId=FEEDBACK_SHEET_ID,
            range='Feedback!A:D',  # Colunas A até D (Data, Avaliação, Pergunta, Resposta)
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        
        print("✅ SUCESSO! Feedback salvo na planilha!")
        print(f"   Linhas atualizadas: {result.get('updates', {}).get('updatedRows', 0)}")
        
        # Verificar se a aba existe
        print("\n🔍 Verificando estrutura da planilha...")
        spreadsheet = service.spreadsheets().get(spreadsheetId=FEEDBACK_SHEET_ID).execute()
        sheets = [sheet['properties']['title'] for sheet in spreadsheet['sheets']]
        print(f"   Abas encontradas: {', '.join(sheets)}")
        
        if 'Feedback' in sheets:
            print("   ✅ Aba 'Feedback' encontrada!")
        else:
            print("   ⚠️  Aba 'Feedback' NÃO encontrada!")
            print("   Execute: python scripts/setup_feedback_sheet.py")
        
        print("\n" + "=" * 60)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        print(f"\n📊 Acesse a planilha:")
        print(f"   https://docs.google.com/spreadsheets/d/{FEEDBACK_SHEET_ID}")
        print(f"   Aba: Feedback")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        print(f"\n🔍 Detalhes do erro:")
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = test_feedback_save()
    sys.exit(0 if success else 1)
