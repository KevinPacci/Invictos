from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from . import crud
from .auth import authenticate_user, get_current_user, get_current_user_id
from .db import get_session, init_db
from .models import (
    AuthResponse,
    BetCreate,
    BetRead,
    BetUpdate,
    SyncResponse,
    UserCreate,
    UserLogin,
    UserRead,
    utcnow,
)
from .security import create_access_token, hash_password
from .settings import get_settings

app = FastAPI(title="Invictos Tracker API", version="0.2.0")
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, session: Session = Depends(get_session)) -> AuthResponse:
    if crud.get_user_by_email(session, payload.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Correo ya registrado")

    hashed_password = hash_password(payload.password)
    try:
        user = crud.create_user(session, payload, hashed_password)
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Correo ya registrado") from exc

    token = create_access_token(subject=user.id)
    return AuthResponse(access_token=token, user=_to_user_read(user))


@app.post("/auth/login", response_model=AuthResponse)
def login_user(payload: UserLogin, session: Session = Depends(get_session)) -> AuthResponse:
    user = authenticate_user(session, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    token = create_access_token(subject=user.id)
    return AuthResponse(access_token=token, user=_to_user_read(user))


@app.get("/auth/me", response_model=UserRead)
def get_me(current_user = Depends(get_current_user)) -> UserRead:
    return _to_user_read(current_user)


@app.get("/bets", response_model=List[BetRead])
def api_list_bets(
    start: Optional[date] = None,
    end: Optional[date] = None,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
) -> List[BetRead]:
    bets = crud.list_bets(session, user_id=user_id, start=start, end=end)
    return [_to_bet_read(bet) for bet in bets]


@app.get("/bets/{bet_id}", response_model=BetRead)
def api_get_bet(
    bet_id: UUID,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
) -> BetRead:
    bet = crud.get_bet(session, bet_id, user_id)
    if not bet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Apuesta no encontrada")
    return _to_bet_read(bet)


@app.post("/bets", response_model=BetRead, status_code=status.HTTP_201_CREATED)
def api_create_bet(
    payload: BetCreate,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
) -> BetRead:
    bet = crud.create_bet(session, payload, user_id)
    return _to_bet_read(bet)


@app.patch("/bets/{bet_id}", response_model=BetRead)
def api_update_bet(
    bet_id: UUID,
    payload: BetUpdate,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
) -> BetRead:
    bet = crud.get_bet(session, bet_id, user_id)
    if not bet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Apuesta no encontrada")
    updated = crud.update_bet(session, bet, payload)
    return _to_bet_read(updated)


@app.delete("/bets/{bet_id}", status_code=status.HTTP_204_NO_CONTENT)
def api_delete_bet(
    bet_id: UUID,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
) -> None:
    bet = crud.get_bet(session, bet_id, user_id)
    if not bet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Apuesta no encontrada")
    crud.delete_bet(session, bet)


@app.get("/sync", response_model=SyncResponse)
def api_sync(
    since: Optional[str] = None,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
) -> SyncResponse:
    parsed_since = _parse_since(since)
    bets = crud.sync_since(session, user_id, parsed_since)
    now = utcnow()
    return SyncResponse(last_sync=now, items=[_to_bet_read(bet) for bet in bets])


def _parse_since(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parámetro 'since' inválido") from exc


def _to_bet_read(bet) -> BetRead:
    if hasattr(BetRead, "model_validate"):
        return BetRead.model_validate(bet)
    return BetRead.from_orm(bet)  # type: ignore[attr-defined]


def _to_user_read(user) -> UserRead:
    if hasattr(UserRead, "model_validate"):
        return UserRead.model_validate(user)
    return UserRead.from_orm(user)  # type: ignore[attr-defined]


__all__ = ["app"]
