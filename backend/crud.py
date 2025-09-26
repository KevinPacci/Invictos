from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from sqlmodel import Session, select

from .models import Bet, BetCreate, BetType, BetUpdate, ParlayLeg, User, UserCreate, utcnow


def _dump(model, **kwargs):
    if hasattr(model, "model_dump"):
        return model.model_dump(**kwargs)
    return model.dict(**kwargs)  # type: ignore[attr-defined]


def list_bets(
    session: Session,
    user_id: UUID,
    start: Optional[date] = None,
    end: Optional[date] = None,
) -> List[Bet]:
    statement = select(Bet).where(Bet.user_id == user_id)
    if start:
        statement = statement.where(Bet.event_date >= start)
    if end:
        statement = statement.where(Bet.event_date <= end)
    statement = statement.order_by(Bet.event_date.desc(), Bet.created_at.desc())
    return session.exec(statement).unique().all()


def get_bet(session: Session, bet_id: UUID, user_id: Optional[UUID] = None) -> Optional[Bet]:
    statement = select(Bet).where(Bet.id == bet_id)
    if user_id is not None:
        statement = statement.where(Bet.user_id == user_id)
    return session.exec(statement).unique().first()


def create_bet(session: Session, payload: BetCreate, user_id: UUID) -> Bet:
    data = _dump(payload, exclude={"legs"}, exclude_none=True)
    bet = Bet(**data, user_id=user_id)
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


def sync_since(session: Session, user_id: UUID, since: Optional[datetime]) -> List[Bet]:
    statement = select(Bet).where(Bet.user_id == user_id)
    if since:
        statement = statement.where(Bet.updated_at >= since)
    statement = statement.order_by(Bet.updated_at)
    return session.exec(statement).unique().all()


def get_user_by_email(session: Session, email: str) -> Optional[User]:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()


def create_user(session: Session, data: UserCreate, password_hash: str) -> User:
    user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=password_hash,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_user(session: Session, user_id: UUID) -> Optional[User]:
    return session.get(User, user_id)


__all__ = [
    "list_bets",
    "get_bet",
    "create_bet",
    "update_bet",
    "delete_bet",
    "sync_since",
    "get_user_by_email",
    "create_user",
    "get_user",
]
