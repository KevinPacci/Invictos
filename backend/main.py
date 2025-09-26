from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from . import crud
from .auth import enforce_api_key
from .db import get_session, init_db
from .models import BetRead, BetCreate, BetUpdate, SyncResponse, utcnow
from .settings import get_settings

app = FastAPI(title="Invictos Tracker API", version="0.1.0")
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/bets", response_model=List[BetRead])
def api_list_bets(
    start: Optional[date] = None,
    end: Optional[date] = None,
    session: Session = Depends(get_session),
    _: None = Depends(enforce_api_key),
) -> List[BetRead]:
    bets = crud.list_bets(session, start=start, end=end)
    return [_to_read(bet) for bet in bets]


@app.get("/bets/{bet_id}", response_model=BetRead)
def api_get_bet(
    bet_id: UUID,
    session: Session = Depends(get_session),
    _: None = Depends(enforce_api_key),
) -> BetRead:
    bet = crud.get_bet(session, bet_id)
    if not bet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Apuesta no encontrada")
    return _to_read(bet)


@app.post("/bets", response_model=BetRead, status_code=status.HTTP_201_CREATED)
def api_create_bet(
    payload: BetCreate,
    session: Session = Depends(get_session),
    _: None = Depends(enforce_api_key),
) -> BetRead:
    bet = crud.create_bet(session, payload)
    return _to_read(bet)


@app.patch("/bets/{bet_id}", response_model=BetRead)
def api_update_bet(
    bet_id: UUID,
    payload: BetUpdate,
    session: Session = Depends(get_session),
    _: None = Depends(enforce_api_key),
) -> BetRead:
    bet = crud.get_bet(session, bet_id)
    if not bet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Apuesta no encontrada")
    updated = crud.update_bet(session, bet, payload)
    return _to_read(updated)


@app.delete("/bets/{bet_id}", status_code=status.HTTP_204_NO_CONTENT)
def api_delete_bet(
    bet_id: UUID,
    session: Session = Depends(get_session),
    _: None = Depends(enforce_api_key),
) -> None:
    bet = crud.get_bet(session, bet_id)
    if not bet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Apuesta no encontrada")
    crud.delete_bet(session, bet)


@app.get("/sync", response_model=SyncResponse)
def api_sync(
    since: Optional[str] = None,
    session: Session = Depends(get_session),
    _: None = Depends(enforce_api_key),
) -> SyncResponse:
    parsed_since = _parse_since(since)
    bets = crud.sync_since(session, parsed_since)
    now = utcnow()
    return SyncResponse(last_sync=now, items=[_to_read(bet) for bet in bets])


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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parametro 'since' invalido") from exc


def _to_read(bet) -> BetRead:
    if hasattr(BetRead, "model_validate"):
        return BetRead.model_validate(bet)
    return BetRead.from_orm(bet)  # type: ignore[attr-defined]


__all__ = ["app"]
