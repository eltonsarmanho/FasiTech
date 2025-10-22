"""Serviço para upload de arquivos no Google Drive."""

import os
from io import BytesIO
from typing import Any, Iterable, Dict

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Importar o carregador de variáveis de ambiente
from src.utils import env_loader
from src.utils.CredentialsEncoder import convertBase64ToJson


def _get_credentials():
    """Obtém as credenciais do Google Cloud a partir da variável de ambiente."""
    credentials_base64 = os.getenv("GOOGLE_CLOUD_CREDENTIALS_FASI_BASE64")
    
    if not credentials_base64:
        credentials_base64 = os.getenv("GOOGLE_CLOUD_CREDENTIALS_BASE64")
    
    if not credentials_base64:
        raise ValueError(
            "Credenciais não encontradas! Configure GOOGLE_CLOUD_CREDENTIALS_FASI_BASE64 "
            "ou GOOGLE_CLOUD_CREDENTIALS_BASE64 no arquivo .env"
        )
    
    credentials_dict = convertBase64ToJson(credentials_base64)
    
    scopes = [
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive'
    ]
    
    credentials = Credentials.from_service_account_info(
        credentials_dict, 
        scopes=scopes
    )
    
    return credentials


def find_or_create_folder(folder_name: str, parent_folder_id: str) -> str:
    """
    Encontra ou cria uma pasta no Google Drive.
    
    Args:
        folder_name: Nome da pasta a ser criada/encontrada
        parent_folder_id: ID da pasta pai
        
    Returns:
        ID da pasta encontrada ou criada
    """
    credentials = _get_credentials()
    service = build('drive', 'v3', credentials=credentials)
    
    # Buscar se a pasta já existe
    query = f"name='{folder_name}' and '{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    
    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    
    folders = results.get('files', [])
    
    if folders:
        print(f"📁 Pasta '{folder_name}' encontrada: {folders[0]['id']}")
        return folders[0]['id']
    
    # Criar pasta se não existir
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_folder_id]
    }
    
    folder = service.files().create(
        body=file_metadata,
        fields='id, name'
    ).execute()
    
    print(f"📂 Pasta '{folder_name}' criada: {folder.get('id')}")
    return folder.get('id')


def upload_files(
    files: Iterable[Any], 
    destination_folder: str,
    turma: str = None,
    matricula: str = None,
    componente: str = None
) -> list[Dict[str, str]]:
    """
    Faz upload de arquivos para o Google Drive com estrutura de pastas.
    
    Args:
        files: Lista de objetos de arquivo (ex: UploadedFile do Streamlit)
        destination_folder: ID da pasta raiz no Google Drive
        turma: Turma do aluno (ex: "2027", "2028")
        matricula: Matrícula do aluno
        componente: Componente curricular (ex: "Plano de Estágio", "Relatório Final")
        
    Returns:
        Lista de dicionários com 'id', 'name' e 'webViewLink' dos arquivos enviados
    """
    if not destination_folder:
        raise ValueError("ID da pasta de destino não fornecido")
    
    try:
        credentials = _get_credentials()
        service = build('drive', 'v3', credentials=credentials)
        
        # Verificar acesso à pasta raiz
        try:
            folder = service.files().get(
                fileId=destination_folder,
                fields='id, name'
            ).execute()
            print(f"📁 Pasta raiz encontrada: {folder.get('name')}")
        except Exception as folder_error:
            error_msg = (
                f"❌ A conta de serviço não tem acesso à pasta do Google Drive.\n"
                f"   Pasta ID: {destination_folder}\n"
                f"   Conta de serviço: contaufpafasi@servicoweb-453121.iam.gserviceaccount.com\n\n"
                f"   SOLUÇÃO:\n"
                f"   1. Acesse: https://drive.google.com/drive/folders/{destination_folder}\n"
                f"   2. Clique com botão direito na pasta > Compartilhar\n"
                f"   3. Adicione: contaufpafasi@servicoweb-453121.iam.gserviceaccount.com\n"
                f"   4. Defina permissão como: Editor\n"
                f"   5. Desmarque 'Notificar pessoas' e clique em Compartilhar\n\n"
                f"   Erro original: {str(folder_error)}"
            )
            raise ValueError(error_msg)
        
        # Criar estrutura de pastas
        target_folder_id = destination_folder
        
        # Se componente for informado, criar pasta do componente primeiro
        if componente:
            target_folder_id = find_or_create_folder(componente, target_folder_id)
        
        if turma:
            # Criar/encontrar pasta da turma
            target_folder_id = find_or_create_folder(turma, target_folder_id)
        
        if matricula:
            # Criar/encontrar pasta da matrícula
            target_folder_id = find_or_create_folder(matricula, target_folder_id)
        
        uploaded_files: list[Dict[str, str]] = []
        
        for file_obj in files:
            # Obter nome e conteúdo do arquivo
            if hasattr(file_obj, 'name'):
                file_name = file_obj.name
            else:
                file_name = "arquivo.pdf"
            
            # Preparar conteúdo do arquivo
            if hasattr(file_obj, 'read'):
                file_content = file_obj.read()
                # Resetar ponteiro se possível
                if hasattr(file_obj, 'seek'):
                    file_obj.seek(0)
            else:
                file_content = file_obj
            
            # Criar BytesIO para upload
            fh = BytesIO(file_content)
            
            # Definir metadados do arquivo
            file_metadata = {
                'name': file_name,
                'parents': [target_folder_id]
            }
            
            # Determinar mimetype
            mimetype = 'application/pdf'
            if hasattr(file_obj, 'type'):
                mimetype = file_obj.type
            
            media = MediaIoBaseUpload(fh, mimetype=mimetype, resumable=True)
            
            # Fazer upload
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
            
            uploaded_files.append({
                'id': file.get('id'),
                'name': file.get('name'),
                'webViewLink': file.get('webViewLink')
            })
            
            print(f"✅ Arquivo '{file_name}' enviado com ID: {file.get('id')}")
            print(f"   Link: {file.get('webViewLink')}")
        
        return uploaded_files
        
    except ValueError:
        # Re-lançar erros de validação com mensagens amigáveis
        raise
    except Exception as e:
        print(f"❌ Erro ao fazer upload para Google Drive: {str(e)}")
        raise


def upload_files_tcc(
    files: Iterable[Any], 
    destination_folder: str,
    componente: str,
    turma: str,
    nome_aluno: str
) -> list[Dict[str, str]]:
    """
    Faz upload de arquivos de TCC para o Google Drive com estrutura hierárquica.
    Estrutura: pasta_raiz / TCC 1 ou TCC 2 / Turma / Nome do Aluno / arquivos
    
    Args:
        files: Lista de objetos de arquivo (ex: UploadedFile do Streamlit)
        destination_folder: ID da pasta raiz do TCC no Google Drive
        componente: "TCC 1" ou "TCC 2"
        turma: Ano da turma (ex: "2027", "2026")
        nome_aluno: Nome completo do aluno
        
    Returns:
        Lista de dicionários com 'id', 'name' e 'webViewLink' dos arquivos enviados
    """
    if not destination_folder:
        raise ValueError("ID da pasta de destino não fornecido")
    
    try:
        credentials = _get_credentials()
        service = build('drive', 'v3', credentials=credentials)
        
        # Verificar acesso à pasta raiz
        try:
            folder = service.files().get(
                fileId=destination_folder,
                fields='id, name'
            ).execute()
            print(f"📁 Pasta raiz TCC encontrada: {folder.get('name')}")
        except Exception as folder_error:
            error_msg = (
                f"❌ A conta de serviço não tem acesso à pasta do Google Drive.\n"
                f"   Pasta ID: {destination_folder}\n"
                f"   Conta de serviço: contaufpafasi@servicoweb-453121.iam.gserviceaccount.com\n\n"
                f"   SOLUÇÃO:\n"
                f"   1. Acesse: https://drive.google.com/drive/folders/{destination_folder}\n"
                f"   2. Clique com botão direito na pasta > Compartilhar\n"
                f"   3. Adicione: contaufpafasi@servicoweb-453121.iam.gserviceaccount.com\n"
                f"   4. Defina permissão como: Editor\n"
                f"   5. Desmarque 'Notificar pessoas' e clique em Compartilhar\n\n"
                f"   Erro original: {str(folder_error)}"
            )
            raise ValueError(error_msg)
        
        # Criar estrutura de pastas hierárquica: raiz / TCC 1 ou TCC 2 / Turma / Nome do Aluno
        target_folder_id = destination_folder
        
        # 1. Criar/encontrar pasta do componente (TCC 1 ou TCC 2)
        print(f"📂 Criando/encontrando pasta: {componente}")
        target_folder_id = find_or_create_folder(componente, target_folder_id)
        
        # 2. Criar/encontrar pasta da turma
        print(f"📂 Criando/encontrando pasta: {turma}")
        target_folder_id = find_or_create_folder(turma, target_folder_id)
        
        # 3. Criar/encontrar pasta com nome do aluno
        print(f"📂 Criando/encontrando pasta: {nome_aluno}")
        target_folder_id = find_or_create_folder(nome_aluno, target_folder_id)
        
        uploaded_files: list[Dict[str, str]] = []
        
        for file_obj in files:
            # Obter nome e conteúdo do arquivo
            if hasattr(file_obj, 'name'):
                file_name = file_obj.name
            else:
                file_name = "arquivo.pdf"
            
            # Preparar conteúdo do arquivo
            if hasattr(file_obj, 'read'):
                file_content = file_obj.read()
                # Resetar ponteiro se possível
                if hasattr(file_obj, 'seek'):
                    file_obj.seek(0)
            else:
                file_content = file_obj
            
            # Criar BytesIO para upload
            fh = BytesIO(file_content)
            
            # Definir metadados do arquivo
            file_metadata = {
                'name': file_name,
                'parents': [target_folder_id]
            }
            
            # Determinar mimetype
            mimetype = 'application/pdf'
            if hasattr(file_obj, 'type'):
                mimetype = file_obj.type
            
            media = MediaIoBaseUpload(fh, mimetype=mimetype, resumable=True)
            
            # Fazer upload
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
            
            uploaded_files.append({
                'id': file.get('id'),
                'name': file.get('name'),
                'webViewLink': file.get('webViewLink')
            })
            
            print(f"✅ Arquivo '{file_name}' enviado com ID: {file.get('id')}")
            print(f"   Link: {file.get('webViewLink')}")
        
        print(f"\n🎉 Estrutura criada: {componente}/{turma}/{nome_aluno}/")
        return uploaded_files
        
    except ValueError:
        # Re-lançar erros de validação com mensagens amigáveis
        raise
    except Exception as e:
        print(f"❌ Erro ao fazer upload TCC para Google Drive: {str(e)}")
        raise
