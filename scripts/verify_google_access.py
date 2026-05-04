#!/usr/bin/env python3
"""
Script para verificar se a conta de serviço tem acesso
à pasta do Google Drive e à planilha do Google Sheets.
"""

import os
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Importar após configurar o path
from src.utils.env_loader import load_environment
from src.utils.CredentialsEncoder import convertBase64ToJson
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Carregar variáveis de ambiente
load_environment()


def _get_credentials():
    """Obtém as credenciais usando o mesmo método dos serviços."""
    credentials_base64 = os.getenv("GOOGLE_CLOUD_CREDENTIALS_FASI_BASE64")
    
    if not credentials_base64:
        credentials_base64 = os.getenv("GOOGLE_CLOUD_CREDENTIALS_BASE64")
    
    if not credentials_base64:
        raise ValueError("Credenciais não encontradas no .env")
    
    # Decodificar usando CredentialsEncoder
    credentials_dict = convertBase64ToJson(credentials_base64)
    
    # Criar credenciais com todos os escopos
    scopes = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/spreadsheets'
    ]
    
    credentials = Credentials.from_service_account_info(
        credentials_dict, 
        scopes=scopes
    )
    
    return credentials

def check_drive_folder_access(folder_id: str) -> bool:
    """Verifica acesso à pasta do Google Drive."""
    print(f"\n🔍 Verificando acesso à pasta do Drive: {folder_id}")
    
    try:
        credentials = _get_credentials()
        service = build('drive', 'v3', credentials=credentials)
        
        # Tentar obter informações da pasta
        folder = service.files().get(
            fileId=folder_id,
            fields='id, name, permissions, owners'
        ).execute()
        
        print(f"✅ Pasta encontrada: '{folder.get('name')}'")
        print(f"   ID: {folder.get('id')}")
        
        # Verificar permissões (se disponível)
        if 'permissions' in folder:
            print("   Permissões:")
            for perm in folder.get('permissions', []):
                role = perm.get('role', 'desconhecido')
                email = perm.get('emailAddress', 'N/A')
                print(f"   - {email}: {role}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO ao acessar pasta: {str(e)}")
        print("\n📋 SOLUÇÃO:")
        print(f"   1. Acesse: https://drive.google.com/drive/folders/{folder_id}")
        print("   2. Clique com botão direito > Compartilhar")
        print("   3. Adicione: contaufpafasi@servicoweb-453121.iam.gserviceaccount.com")
        print("   4. Defina permissão: Editor")
        print("   5. Desmarque 'Notificar pessoas' e clique em Compartilhar")
        return False


def check_sheet_access(sheet_id: str) -> bool:
    """Verifica acesso à planilha do Google Sheets."""
    print(f"\n🔍 Verificando acesso à planilha: {sheet_id}")
    
    try:
        credentials = _get_credentials()
        service = build('sheets', 'v4', credentials=credentials)
        
        # Tentar obter informações da planilha
        sheet = service.spreadsheets().get(
            spreadsheetId=sheet_id,
            fields='properties,sheets'
        ).execute()
        
        title = sheet.get('properties', {}).get('title', 'Sem título')
        print(f"✅ Planilha encontrada: '{title}'")
        print(f"   ID: {sheet_id}")
        
        # Listar abas
        sheets_list = sheet.get('sheets', [])
        if sheets_list:
            print("   Abas disponíveis:")
            for s in sheets_list:
                sheet_title = s.get('properties', {}).get('title', 'Sem nome')
                print(f"   - {sheet_title}")
        
        # Verificar se existe "Respostas ao formulário 1" (nome padrão usado)
        target_sheet = "Respostas ao formulário 1"
        sheet_exists = any(
            s.get('properties', {}).get('title') == target_sheet
            for s in sheets_list
        )
        
        if not sheet_exists:
            print(f"\n⚠️  AVISO: Não encontrei aba '{target_sheet}'")
            print(f"   Por favor, certifique-se de que existe uma aba com este nome")
            print("   Ou atualize o parâmetro range_name em src/services/google_sheets.py")
        else:
            print(f"\n✅ Aba '{target_sheet}' encontrada e pronta para uso")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO ao acessar planilha: {str(e)}")
        print("\n📋 SOLUÇÃO:")
        print(f"   1. Acesse: https://docs.google.com/spreadsheets/d/{sheet_id}")
        print("   2. Clique em 'Compartilhar' (botão verde)")
        print("   3. Adicione: contaufpafasi@servicoweb-453121.iam.gserviceaccount.com")
        print("   4. Defina permissão: Editor")
        print("   5. Desmarque 'Notificar pessoas' e clique em Compartilhar")
        return False


def main():
    """Executa todas as verificações."""
    print("=" * 70)
    print("🔐 Verificação de Acesso aos Recursos do Google")
    print("=" * 70)
    
    # Obter IDs dos recursos
    folder_id = os.getenv("ACC_FOLDER_ID", "17GiNzOq0yWsvDNKlIx5672ya_qviGOto")
    sheet_id = os.getenv("SHEET_ID", "1QtSUY5oyYdaVDBPnRuFOxJQDuL8Y73B-pt_e24Y0yGw")
    
    print(f"\n📁 Pasta do Drive: {folder_id}")
    print(f"📊 Planilha: {sheet_id}")
    print(f"🔑 Conta de serviço: contaufpafasi@servicoweb-453121.iam.gserviceaccount.com")
    
    # Verificar credenciais
    print("\n🔍 Verificando credenciais...")
    creds_var = os.getenv("GOOGLE_CLOUD_CREDENTIALS_FASI_BASE64")
    if not creds_var:
        creds_var = os.getenv("GOOGLE_CLOUD_CREDENTIALS_BASE64")
    
    if not creds_var:
        print("❌ ERRO: Credenciais não encontradas no .env")
        print("   Verifique se GOOGLE_CLOUD_CREDENTIALS_FASI_BASE64 está configurado")
        sys.exit(1)
    
    print(f"✅ Credenciais encontradas ({len(creds_var)} caracteres)")
    
    # Executar verificações
    results = []
    
    results.append(("Pasta do Drive", check_drive_folder_access(folder_id)))
    results.append(("Planilha", check_sheet_access(sheet_id)))
    
    # Resumo
    print("\n" + "=" * 70)
    print("📊 RESUMO DAS VERIFICAÇÕES")
    print("=" * 70)
    
    all_ok = True
    for name, status in results:
        symbol = "✅" if status else "❌"
        print(f"{symbol} {name}: {'OK' if status else 'FALHOU'}")
        if not status:
            all_ok = False
    
    print("=" * 70)
    
    if all_ok:
        print("\n🎉 Tudo certo! O sistema está pronto para usar.")
        print("   Execute: streamlit run src/app/main.py")
        sys.exit(0)
    else:
        print("\n⚠️  Há problemas que precisam ser corrigidos.")
        print("   Siga as instruções acima para compartilhar os recursos.")
        print("   Consulte: GOOGLE_SETUP.md para mais detalhes")
        sys.exit(1)


if __name__ == "__main__":
    main()
