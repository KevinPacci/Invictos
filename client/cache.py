from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Optional

from .config import get_client_config
from .models import AuthResponse, Bet, serialize_bets


def load_cached_bets(user_id: str) -> List[Bet]:
    cfg = get_client_config()
    file = cfg.bets_cache_path(user_id)
    if not file.exists():
        return []
    try:
        raw = json.loads(file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return [Bet.from_dict(item) for item in raw]


def save_cached_bets(bets: Iterable[Bet], user_id: str) -> None:
    cfg = get_client_config()
    data = serialize_bets(bets)
    cfg.bets_cache_path(user_id).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_pending_queue(user_id: str) -> List[dict]:
    cfg = get_client_config()
    file = cfg.queue_path(user_id)
    if not file.exists():
        return []
    try:
        return json.loads(file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def save_pending_queue(items: Iterable[dict], user_id: str) -> None:
    cfg = get_client_config()
    cfg.queue_path(user_id).write_text(json.dumps(list(items), ensure_ascii=False, indent=2), encoding="utf-8")


def append_pending_op(op: dict, user_id: str) -> None:
    queue = load_pending_queue(user_id)
    queue.append(op)
    save_pending_queue(queue, user_id)


def load_auth() -> Optional[AuthResponse]:
    cfg = get_client_config()
    file = cfg.auth_path
    if not file.exists():
        return None
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return AuthResponse.from_dict(data)


def save_auth(auth: Optional[AuthResponse]) -> None:
    cfg = get_client_config()
    if auth is None:
        if cfg.auth_path.exists():
            cfg.auth_path.unlink()
        return
    cfg.auth_path.write_text(json.dumps(auth.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


__all__ = [
    "load_cached_bets",
    "save_cached_bets",
    "load_pending_queue",
    "save_pending_queue",
    "append_pending_op",
    "load_auth",
    "save_auth",
]
