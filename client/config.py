from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass
class ClientConfig:
    api_url: str
    api_key: str | None
    cache_dir: Path
    sync_interval_seconds: int = 120

    @property
    def cache_file(self) -> Path:
        return self.cache_dir / "bets_cache.json"

    @property
    def queue_file(self) -> Path:
        return self.cache_dir / "pending_ops.json"


@lru_cache
def get_client_config() -> ClientConfig:
    base = os.getenv("INVICTOS_CACHE_DIR")
    cache_dir = Path(base) if base else Path.home() / ".invictos"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return ClientConfig(
        api_url=os.getenv("INVICTOS_API_URL", "http://127.0.0.1:8000"),
        api_key=os.getenv("INVICTOS_API_KEY"),
        cache_dir=cache_dir,
        sync_interval_seconds=int(os.getenv("INVICTOS_SYNC_INTERVAL", "180")),
    )


__all__ = ["ClientConfig", "get_client_config"]
