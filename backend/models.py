from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import ConfigDict
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel


class BetType(str, Enum):
    SINGLE = "single"
    PARLAY = "parlay"


class BetOutcome(str, Enum):
    WIN = "acertada"
    LOSS = "fallida"
    PENDING = "pendiente"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ParlayLegBase(SQLModel):
    detail: str = Field(max_length=255)
    odds: float = Field(gt=1)


class BetBase(SQLModel):
    event_date: date = Field(index=True)
    type: BetType = Field(default=BetType.SINGLE)
    detail: str = Field(max_length=512)
    stake: float = Field(gt=0)
    odds: float = Field(gt=1)
    cashout: Optional[float] = Field(default=None, ge=0)
    outcome: BetOutcome = Field(default=BetOutcome.PENDING)


class Bet(BetBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow, index=True)

    legs: list["ParlayLeg"] = Relationship(
        back_populates="bet",
        sa_relationship=relationship(
            "ParlayLeg",
            back_populates="bet",
            cascade="all, delete-orphan",
            lazy="joined",
        ),
    )


class ParlayLeg(ParlayLegBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    bet_id: UUID = Field(foreign_key="bet.id", index=True)
    created_at: datetime = Field(default_factory=utcnow)

    bet: "Bet" = Relationship(
        back_populates="legs",
        sa_relationship=relationship("Bet", back_populates="legs"),
    )


class ParlayLegRead(ParlayLegBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class BetRead(BetBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
    legs: list[ParlayLegRead] = Field(default_factory=list)


class BetCreate(BetBase):
    id: Optional[UUID] = None
    legs: list[ParlayLegBase] = Field(default_factory=list)


class BetUpdate(SQLModel):
    event_date: Optional[date] = None
    type: Optional[BetType] = None
    detail: Optional[str] = None
    stake: Optional[float] = Field(default=None, gt=0)
    odds: Optional[float] = Field(default=None, gt=1)
    cashout: Optional[float] = Field(default=None, ge=0)
    outcome: Optional[BetOutcome] = None
    legs: Optional[list[ParlayLegBase]] = None


class SyncResponse(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    last_sync: datetime
    items: list[BetRead]


__all__ = [
    "Bet",
    "BetBase",
    "BetCreate",
    "BetOutcome",
    "BetRead",
    "BetType",
    "BetUpdate",
    "ParlayLeg",
    "ParlayLegBase",
    "ParlayLegRead",
    "SyncResponse",
]
