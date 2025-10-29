from __future__ import annotations

import os
import secrets
import hashlib
from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Configurar bearer token security
security = HTTPBearer()

# API Keys válidas (em produção, isso deveria vir de um banco de dados)
# Formato: hash_da_api_key -> {"name": "nome_do_cliente", "permissions": ["read", "write"]}
VALID_API_KEYS = {
    # API Key de exemplo: "fasitech_api_2024_social_data"
    # Hash SHA256: d1ac8c57fff03a9359165341dde28d3ee17f1a368566dbbc91b52c9bbc92caa6
    "d1ac8c57fff03a9359165341dde28d3ee17f1a368566dbbc91b52c9bbc92caa6": {
        "name": "FasiTech Social API Client",
        "permissions": ["read"]
    }
}

# Carregamento de API keys do ambiente
def load_api_keys_from_env():
    """Carrega API keys adicionais das variáveis de ambiente."""
    env_keys = os.getenv("FASITECH_API_KEYS", "")
    if env_keys:
        for key_pair in env_keys.split(","):
            if ":" in key_pair:
                key, name = key_pair.split(":", 1)
                key_hash = hashlib.sha256(key.strip().encode()).hexdigest()
                VALID_API_KEYS[key_hash] = {
                    "name": name.strip(),
                    "permissions": ["read"]
                }

# Carregar keys do ambiente na inicialização
load_api_keys_from_env()


def hash_api_key(api_key: str) -> str:
    """Gera hash SHA256 de uma API key."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key() -> tuple[str, str]:
    """
    Gera uma nova API key segura.
    
    Returns:
        Tupla com (api_key, hash_da_api_key)
    """
    api_key = f"fasitech_{secrets.token_urlsafe(32)}"
    key_hash = hash_api_key(api_key)
    return api_key, key_hash


def validate_api_key(api_key: str) -> Optional[dict]:
    """
    Valida uma API key e retorna informações do cliente.
    
    Args:
        api_key: A API key a ser validada
        
    Returns:
        Informações do cliente se válida, None caso contrário
    """
    if not api_key:
        return None
    
    key_hash = hash_api_key(api_key)
    return VALID_API_KEYS.get(key_hash)


def require_api_key(
    authorization: Optional[str] = Header(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """
    Valida API key via Bearer token ou header X-API-Key.
    
    Suporta dois formatos:
    1. Authorization: Bearer <api_key>
    2. X-API-Key: <api_key>
    
    Args:
        authorization: Header Authorization opcional
        credentials: Credenciais Bearer token
        
    Returns:
        Informações do cliente autenticado
        
    Raises:
        HTTPException: Se a API key for inválida ou não fornecida
    """
    api_key = None
    
    # Tentar obter API key do Bearer token
    if credentials:
        api_key = credentials.credentials
    
    # Se não encontrou no Bearer, tentar no header X-API-Key
    if not api_key and authorization:
        if authorization.startswith("Bearer "):
            api_key = authorization[7:]  # Remove "Bearer "
        else:
            api_key = authorization  # Assume que é diretamente a API key
    
    # Validar API key
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key é obrigatória. Use Authorization: Bearer <api_key> ou X-API-Key: <api_key>",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    client_info = validate_api_key(api_key)
    if not client_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválida",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return client_info


def require_permission(required_permission: str):
    """
    Decorator para exigir permissão específica.
    
    Args:
        required_permission: Permissão necessária (ex: "read", "write")
    """
    def permission_checker(client_info: dict = Depends(require_api_key)) -> dict:
        permissions = client_info.get("permissions", [])
        if required_permission not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão '{required_permission}' necessária"
            )
        return client_info
    
    return permission_checker
