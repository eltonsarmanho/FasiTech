"""Serviço para processamento e sanitização de dados de formulários."""

import re
from typing import Dict, Any, Iterable


def sanitize_cpf(cpf: str) -> str:
    """
    Remove caracteres não numéricos do CPF.
    
    Args:
        cpf: CPF com ou sem formatação
        
    Returns:
        CPF apenas com números
    """
    if not cpf:
        return ""
    return re.sub(r'\D', '', cpf)


def sanitize_text_field(text: str) -> str:
    """
    Remove espaços extras e caracteres especiais de campos de texto.
    
    Args:
        text: Texto a ser sanitizado
        
    Returns:
        Texto sanitizado
    """
    if not text:
        return ""
    
    # Remove espaços extras no início e fim
    text = text.strip()
    
    # Remove múltiplos espaços internos
    text = re.sub(r'\s+', ' ', text)
    
    return text


def sanitize_submission(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitiza dados de submissão de formulário ACC.
    
    Args:
        form_data: Dicionário com os dados do formulário
        
    Returns:
        Dicionário com dados sanitizados
    """
    sanitized = {}
    
    # Sanitizar campos de texto
    for key in ['name', 'email', 'class_group', 'registration']:
        value = form_data.get(key, '')
        if isinstance(value, str):
            if key == 'registration':
                # Remove caracteres não alfanuméricos de matrícula
                sanitized[key] = re.sub(r'[^a-zA-Z0-9]', '', value.strip())
            else:
                sanitized[key] = sanitize_text_field(value)
        else:
            sanitized[key] = value
    
    return sanitized


def prepare_files(files: Iterable[Any]) -> Iterable[Any]:
    """
    Prepara arquivos para upload, validando e filtrando.
    
    Args:
        files: Lista de arquivos (ex: UploadedFile do Streamlit)
        
    Yields:
        Arquivos válidos prontos para upload
    """
    if not files:
        return
    
    for file_obj in files:
        # Verificar se o arquivo existe e tem nome
        if file_obj is None:
            continue
            
        if not hasattr(file_obj, 'name') or not file_obj.name:
            continue
        
        # Validar extensão do arquivo (apenas PDF por padrão)
        if not validate_file_extension(file_obj.name, ['.pdf']):
            print(f"⚠️ Arquivo '{file_obj.name}' ignorado - apenas PDF permitido")
            continue
        
        # Validar tamanho do arquivo
        if hasattr(file_obj, 'size'):
            if not validate_file_size(file_obj.size, max_size_mb=10):
                print(f"⚠️ Arquivo '{file_obj.name}' ignorado - tamanho excede 10MB")
                continue
        
        yield file_obj


def process_form_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processa e sanitiza dados de um formulário.
    
    Args:
        data: Dicionário com os dados do formulário
        
    Returns:
        Dicionário com dados processados e sanitizados
    """
    processed_data = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            # Sanitizar campos de texto
            if key.lower() in ['cpf', 'matricula']:
                processed_data[key] = sanitize_cpf(value)
            else:
                processed_data[key] = sanitize_text_field(value)
        else:
            processed_data[key] = value
    
    return processed_data


def validate_file_size(file_size: int, max_size_mb: int = 10) -> bool:
    """
    Valida o tamanho de um arquivo.
    
    Args:
        file_size: Tamanho do arquivo em bytes
        max_size_mb: Tamanho máximo permitido em MB
        
    Returns:
        True se o arquivo está dentro do limite, False caso contrário
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes


def validate_file_extension(filename: str, allowed_extensions: list = None) -> bool:
    """
    Valida a extensão de um arquivo.
    
    Args:
        filename: Nome do arquivo
        allowed_extensions: Lista de extensões permitidas (ex: ['.pdf', '.doc'])
        
    Returns:
        True se a extensão é permitida, False caso contrário
    """
    if allowed_extensions is None:
        allowed_extensions = ['.pdf']
    
    if not filename:
        return False
    
    file_ext = filename.lower().split('.')[-1]
    file_ext_with_dot = f'.{file_ext}'
    
    return file_ext_with_dot in [ext.lower() for ext in allowed_extensions]

