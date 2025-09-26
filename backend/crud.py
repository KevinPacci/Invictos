from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from sqlmodel import Session, select

from .models import Bet, BetCreate, BetType, BetUpdate, ParlayLeg, utcnow


def _dump(model, **kwargs):
    if hasattr(model, "model_dump"):
        return model.model_dump(**kwargs)
    return model.dict(**kwargs)  # type: ignore[attr-defined]


def list_bets(session: Session, start: Optional[date] = None, end: Optional[date] = None) -> List[Bet]:
    statement = select(Bet)
    if start:
        statement = statement.where(Bet.event_date >= start)
    if end:
        statement = statement.where(Bet.event_date <= end)
    statement = statement.order_by(Bet.event_date.desc(), Bet.created_at.desc())
    return session.exec(statement).unique().all()


def get_bet(session: Session, bet_id: UUID) -> Optional[Bet]:
    return session.get(Bet, bet_id)


def create_bet(session: Session, payload: BetCreate) -> Bet:
    data = _dump(payload, exclude={"legs"}, exclude_none=True)
    bet = Bet(**data)
    bet.updated_at = utcnow()
    if bet.type == BetType.PARLAY and payload.legs:
        bet.legs = [ParlayLeg(**_dump(leg)) for leg in payload.legs]
    session.add(bet)
    session.commit()
    session.refresh(bet)
    return bet


def update_bet(session: Session, bet: Bet, payload: BetUpdate) -> Bet:
    data = _dump(payload, exclude_unset=True, exclude_none=True, exclude={"legs"})
    for key, value in data.items():
        setattr(bet, key, value)
    if payload.legs is not None:
        bet.legs.clear()
        if bet.type == BetType.PARLAY:
            for leg in payload.legs:
                bet.legs.append(ParlayLeg(**_dump(leg)))
    bet.updated_at = utcnow()
    session.add(bet)
    session.commit()
    session.refresh(bet)
    return bet


def delete_bet(session: Session, bet: Bet) -> None:
    session.delete(bet)
    session.commit()


def sync_since(session: Session, since: Optional[datetime]) -> List[Bet]:
    statement = select(Bet)
    if since:
        statement = statement.where(Bet.updated_at >= since)
    statement = statement.order_by(Bet.updated_at)
    return session.exec(statement).unique().all()


__all__ = [
    "list_bets",
    "get_bet",
    "create_bet",
    "update_bet",
    "delete_bet",
    "sync_since",
]
