from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Iterable, List, Optional


@dataclass(slots=True)
class ParlayLeg:
    id: str
    detail: str
    odds: float

    @classmethod
    def from_dict(cls, data: dict) -> "ParlayLeg":
        return cls(
            id=str(data.get("id")),
            detail=data.get("detail", ""),
            odds=float(data.get("odds", 0.0)),
        )

    def to_dict(self) -> dict:
        return {"id": self.id, "detail": self.detail, "odds": self.odds}

    def to_payload(self) -> dict:
        return {"detail": self.detail, "odds": self.odds}


@dataclass(slots=True)
class Bet:
    id: str
    user_id: str
    event_date: date
    type: str
    detail: str
    stake: float
    odds: float
    cashout: Optional[float]
    outcome: str
    legs: List[ParlayLeg] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_dict(cls, data: dict) -> "Bet":
        return cls(
            id=str(data.get("id")),
            user_id=str(data.get("user_id")),
            event_date=_parse_date(data.get("event_date")),
            type=str(data.get("type", "single")),
            detail=data.get("detail", ""),
            stake=float(data.get("stake", 0.0)),
            odds=float(data.get("odds", 1.0)),
            cashout=_parse_optional_float(data.get("cashout")),
            outcome=str(data.get("outcome", "pendiente")),
            legs=[ParlayLeg.from_dict(item) for item in data.get("legs", [])],
            created_at=_parse_datetime(data.get("created_at")),
            updated_at=_parse_datetime(data.get("updated_at")),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_date": self.event_date.isoformat(),
            "type": self.type,
            "detail": self.detail,
            "stake": self.stake,
            "odds": self.odds,
            "cashout": self.cashout,
            "outcome": self.outcome,
            "legs": [leg.to_dict() for leg in self.legs],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def to_payload(self) -> dict:
        return {
            "event_date": self.event_date.isoformat(),
            "type": self.type,
            "detail": self.detail,
            "stake": self.stake,
            "odds": self.odds,
            "cashout": self.cashout,
            "outcome": self.outcome,
            "legs": [leg.to_payload() for leg in self.legs],
        }

    def gross_return(self) -> float:
        if self.cashout is not None:
            return self.cashout
        if self.outcome == "acertada":
            return self.stake * self.odds
        return 0.0

    def net(self) -> float:
        return self.gross_return() - self.stake


@dataclass(slots=True)
class User:
    id: str
    email: str
    full_name: Optional[str]
    created_at: datetime

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        return cls(
            id=str(data.get("id")),
            email=data.get("email", ""),
            full_name=data.get("full_name"),
            created_at=_parse_datetime(data.get("created_at")),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(slots=True)
class AuthResponse:
    access_token: str
    token_type: str
    user: User

    @classmethod
    def from_dict(cls, data: dict) -> "AuthResponse":
        return cls(
            access_token=data.get("access_token", ""),
            token_type=data.get("token_type", "bearer"),
            user=User.from_dict(data.get("user", {})),
        )

    def to_dict(self) -> dict:
        return {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "user": self.user.to_dict(),
        }


def _parse_date(value) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        return date.fromisoformat(value[:10])
    raise ValueError(f"No se puede convertir a fecha: {value!r}")


def _parse_datetime(value) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            pass
    return datetime.utcnow()


def _parse_optional_float(value) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def serialize_bets(items: Iterable[Bet]) -> List[dict]:
    return [item.to_dict() for item in items]


__all__ = [
    "AuthResponse",
    "Bet",
    "ParlayLeg",
    "User",
    "serialize_bets",
]
