from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass
class ClientConfig:
    api_url: str
    cache_root: Path
    sync_interval_seconds: int = 180

    def ensure_user_dir(self, user_id: str) -> Path:
        path = self.cache_root / user_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def bets_cache_path(self, user_id: str) -> Path:
        return self.ensure_user_dir(user_id) / "bets_cache.json"

    def queue_path(self, user_id: str) -> Path:
        return self.ensure_user_dir(user_id) / "pending_ops.json"

    @property
    def auth_path(self) -> Path:
        return self.cache_root / "auth.json"


@lru_cache
def get_client_config() -> ClientConfig:
    base = os.getenv("INVICTOS_CACHE_DIR")
    cache_root = Path(base) if base else Path.home() / ".invictos"
    cache_root.mkdir(parents=True, exist_ok=True)
    return ClientConfig(
        api_url=os.getenv("INVICTOS_API_URL", "http://127.0.0.1:8000"),
        cache_root=cache_root,
        sync_interval_seconds=int(os.getenv("INVICTOS_SYNC_INTERVAL", "180")),
    )


__all__ = ["ClientConfig", "get_client_config"]
