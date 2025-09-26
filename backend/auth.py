from __future__ import annotations

from fastapi import Header, HTTPException, status

from .settings import get_settings


async def enforce_api_key(x_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if not settings.api_key:
        return
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key requerida")


__all__ = ["enforce_api_key"]
