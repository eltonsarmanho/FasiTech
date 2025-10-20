from __future__ import annotations

from fastapi import Depends

from src.middleware.auth import require_api_key


def get_auth_dependency(_: None = Depends(require_api_key)) -> None:
    """Encapsula dependências de autenticação para rotas."""
    return None
