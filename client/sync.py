from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List

from . import cache
from .api import ApiClient, ApiClientError, ApiConnectionError
from .models import Bet


@dataclass
class PendingOperation:
    kind: str
    bet_id: str
    payload: Dict[str, Any]
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PendingOperation":
        return cls(
            kind=data.get("kind", ""),
            bet_id=str(data.get("bet_id")),
            payload=data.get("payload", {}),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
        )


def enqueue_operation(kind: str, bet: Bet | None, payload: Dict[str, Any]) -> None:
    op = PendingOperation(
        kind=kind,
        bet_id=bet.id if bet else payload.get("bet_id", ""),
        payload=payload,
        created_at=datetime.utcnow().isoformat(),
    )
    cache.append_pending_op(op.to_dict())


def flush_pending(client: ApiClient, state) -> None:
    queue_raw = cache.load_pending_queue()
    if not queue_raw:
        return

    pending = [PendingOperation.from_dict(item) for item in queue_raw]
    applied: List[Dict[str, Any]] = []
    try:
        for op in pending:
            if op.kind == "create":
                bet = Bet.from_dict(op.payload)
                created = client.create_bet(bet)
                state.upsert(created)
            elif op.kind == "update":
                bet_id = op.payload.get("bet_id") or op.bet_id
                patch = op.payload.get("data", {})
                updated = client.update_bet(bet_id, patch)
                state.upsert(updated)
            elif op.kind == "delete":
                bet_id = op.payload.get("bet_id") or op.bet_id
                client.delete_bet(bet_id)
                state.remove(bet_id)
            applied.append(op.to_dict())
    except (ApiClientError, ApiConnectionError):
        remaining = [item for item in queue_raw if item not in applied]
        cache.save_pending_queue(remaining)
        return

    cache.save_pending_queue([])


__all__ = ["enqueue_operation", "flush_pending"]
