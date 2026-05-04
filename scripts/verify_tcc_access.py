#!/usr/bin/env python3
"""Script para verificar acesso às configurações do TCC no Google Drive e Sheets."""

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
        "https://www.googleapis.com/auth/drive",
    ]
    
    credentials = service_account.Credentials.from_service_account_info(
        credentials_json, scopes=scopes
    )
    
    return credentials


def check_drive_folder_access(folder_id: str):
    """Verifica acesso à pasta do Google Drive."""
    try:
        credentials = get_credentials()
        service = build("drive", "v3", credentials=credentials)
        
        print(f"🔍 Verificando acesso à pasta do Drive: {folder_id}")
        
        # Buscar informações da pasta
        folder = service.files().get(
            fileId=folder_id,
            fields="id, name, permissions, mimeType, webViewLink"
        ).execute()
        
        print(f"✅ Pasta encontrada: {folder.get('name')}")
        print(f"   ID: {folder.get('id')}")
        print(f"   Tipo: {folder.get('mimeType')}")
        print(f"   Link: {folder.get('webViewLink')}")
        
        # Verificar permissões
        permissions = folder.get('permissions', [])
        if permissions:
            print(f"   Permissões:")
            for perm in permissions:
                role = perm.get('role', 'N/A')
                perm_type = perm.get('type', 'N/A')
                email = perm.get('emailAddress', 'N/A')
                print(f"      - {perm_type}: {email} ({role})")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao acessar pasta do Drive: {str(e)}")
        return False


def check_sheet_access(sheet_id: str, tab_name: str = "Respostas TCC"):
    """Verifica acesso à planilha do Google Sheets."""
    try:
        credentials = get_credentials()
        service = build("sheets", "v4", credentials=credentials)
        
        print(f"\n🔍 Verificando acesso à planilha: {sheet_id}")
        
        # Buscar informações da planilha
        spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        
        print(f"✅ Planilha encontrada: {spreadsheet.get('properties', {}).get('title')}")
        print(f"   ID: {sheet_id}")
        print(f"   Link: https://docs.google.com/spreadsheets/d/{sheet_id}/edit")
        
        # Listar abas
        sheets = spreadsheet.get('sheets', [])
        print(f"   Abas ({len(sheets)}):")
        
        tab_exists = False
        for sheet in sheets:
            title = sheet['properties']['title']
            sheet_id_number = sheet['properties']['sheetId']
            print(f"      - {title} (ID: {sheet_id_number})")
            if title == tab_name:
                tab_exists = True
        
        if tab_exists:
            print(f"\n✅ Aba '{tab_name}' encontrada!")
            
            # Verificar cabeçalhos
            range_name = f"{tab_name}!A1:J1"
            result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if values:
                print(f"   Cabeçalhos:")
                for idx, header in enumerate(values[0], 1):
                    print(f"      {idx}. {header}")
        else:
            print(f"\n⚠️  Aba '{tab_name}' NÃO encontrada!")
            print(f"   Execute: python scripts/setup_tcc_sheet.py")
        
        return tab_exists
        
    except Exception as e:
        print(f"❌ Erro ao acessar planilha: {str(e)}")
        return False


def main():
    """Função principal."""
    print("=" * 70)
    print("🔐 Verificação de Acesso - Configurações TCC")
    print("=" * 70)
    print()
    
    # Configurações do TCC (do secrets.toml)
    TCC_DRIVE_FOLDER_ID = "1lQmh3nV26OUsXhD118qts-QV0-vYieqR"
    TCC_SHEET_ID = "1D21Nn3w6v5LW9UOotxkqPK-6NSs7OETy7RjH51ur2do"
    
    # Verificar Drive
    drive_ok = check_drive_folder_access(TCC_DRIVE_FOLDER_ID)
    
    # Verificar Sheets
    sheet_ok = check_sheet_access(TCC_SHEET_ID, "Respostas TCC")
    
    # Resumo final
    print()
    print("=" * 70)
    print("📊 Resumo da Verificação")
    print("=" * 70)
    print(f"Google Drive: {'✅ OK' if drive_ok else '❌ ERRO'}")
    print(f"Google Sheets: {'✅ OK' if sheet_ok else '❌ ERRO'}")
    
    if drive_ok and sheet_ok:
        print()
        print("🎉 Tudo pronto! O FormTCC está configurado corretamente.")
        print()
        print("🚀 Próximos passos:")
        print("   1. Execute: streamlit run src/app/main.py")
        print("   2. Acesse o Formulário TCC")
        print("   3. Teste uma submissão")
    else:
        print()
        print("⚠️  Existem problemas de configuração.")
        print()
        print("🔧 Soluções:")
        if not drive_ok:
            print("   - Compartilhe a pasta TCC com: contaufpafasi@servicoweb-453121.iam.gserviceaccount.com")
        if not sheet_ok:
            print("   - Compartilhe a planilha com: contaufpafasi@servicoweb-453121.iam.gserviceaccount.com")
            print("   - Verifique se a aba 'Respostas TCC' existe")
    
    print("=" * 70)


if __name__ == "__main__":
    main()
