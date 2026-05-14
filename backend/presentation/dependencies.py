from __future__ import annotations

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

from backend.config.settings import settings

_api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


def _extract_token(raw: str | None) -> str:
    if not raw:
        return ""
    return raw.removeprefix("Bearer ").strip()


async def get_auth_dependency(raw: str | None = Security(_api_key_header)) -> str:
    token = _extract_token(raw)
    if not settings.api_key or token == settings.api_key:
        return token
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")


async def get_admin_dependency(raw: str | None = Security(_api_key_header)) -> str:
    token = _extract_token(raw)
    valid_tokens = set(settings.admin_keys_list)
    if settings.fasi_token:
        valid_tokens.add(settings.fasi_token)
    if token in valid_tokens:
        return token
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito")


async def get_raw_social_read_permission(raw: str | None = Security(_api_key_header)) -> str:
    token = _extract_token(raw)
    valid = settings.raw_social_api_key or settings.api_key
    if token == valid:
        return token
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
