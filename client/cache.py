from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

from .config import get_client_config
from .models import Bet, serialize_bets


def load_cached_bets() -> List[Bet]:
    cfg = get_client_config()
    file = cfg.cache_file
    if not file.exists():
        return []
    try:
        raw = json.loads(file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return [Bet.from_dict(item) for item in raw]


def save_cached_bets(bets: Iterable[Bet]) -> None:
    cfg = get_client_config()
    data = serialize_bets(bets)
    cfg.cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_pending_queue() -> List[dict]:
    cfg = get_client_config()
    file = cfg.queue_file
    if not file.exists():
        return []
    try:
        return json.loads(file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def save_pending_queue(items: Iterable[dict]) -> None:
    cfg = get_client_config()
    cfg.queue_file.write_text(json.dumps(list(items), ensure_ascii=False, indent=2), encoding="utf-8")


def append_pending_op(op: dict) -> None:
    queue = load_pending_queue()
    queue.append(op)
    save_pending_queue(queue)


__all__ = [
    "load_cached_bets",
    "save_cached_bets",
    "load_pending_queue",
    "save_pending_queue",
    "append_pending_op",
]
