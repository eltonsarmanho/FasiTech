from __future__ import annotations

from fastapi import Depends

from src.middleware.auth import require_api_key, require_permission


def get_auth_dependency(client_info: dict = Depends(require_api_key)) -> dict:
    """
    Dependência básica de autenticação para rotas.
    
    Returns:
        Informações do cliente autenticado
    """
    return client_info


def get_read_permission(client_info: dict = Depends(require_permission("read"))) -> dict:
    """
    Dependência que exige permissão de leitura.
    
    Returns:
        Informações do cliente autenticado com permissão de leitura
    """
    return client_info


def get_write_permission(client_info: dict = Depends(require_permission("write"))) -> dict:
    """
    Dependência que exige permissão de escrita.
    
    Returns:
        Informações do cliente autenticado com permissão de escrita
    """
    return client_info
