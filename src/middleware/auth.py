from __future__ import annotations

from fastapi import Depends, HTTPException, status


def require_api_key(api_key: str = Depends(lambda: "")) -> None:
    """Placeholder simples para validação de API key."""
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
