from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List


@dataclass
class Settings:
    """Simple settings object driven by environment variables."""

    database_url: str = field(default_factory=lambda: os.getenv("INVICTOS_DB_URL", "sqlite:///./invictos.db"))
    api_key: str | None = field(default_factory=lambda: os.getenv("INVICTOS_API_KEY"))
    allowed_origins: List[str] = field(
        default_factory=lambda: _parse_origins(os.getenv("INVICTOS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"))
    )

    @property
    def sync_enabled(self) -> bool:
        return bool(self.api_key)


def _parse_origins(raw: str) -> List[str]:
    values = [item.strip() for item in raw.split(",") if item.strip()]
    return values or ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


__all__ = ["Settings", "get_settings"]
