from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, Iterable, List, Optional

from .models import Bet, User


@dataclass
class SummaryMetrics:
    stake_total: float = 0.0
    return_total: float = 0.0
    net: float = 0.0
    wins: int = 0
    losses: int = 0
    pending: int = 0
    count: int = 0

    @property
    def yield_percent(self) -> float:
        if self.stake_total <= 0:
            return 0.0
        return (self.net / self.stake_total) * 100


class AppState:
    def __init__(self, bets: Optional[Iterable[Bet]] = None, user: Optional[User] = None) -> None:
        self.bets: Dict[str, Bet] = {}
        if bets:
            for bet in bets:
                self.bets[bet.id] = bet
        self.last_sync: Optional[datetime] = None
        self.user: Optional[User] = user

    @property
    def user_id(self) -> Optional[str]:
        return self.user.id if self.user else None

    def set_user(self, user: Optional[User]) -> None:
        self.user = user

    def upsert(self, bet: Bet) -> None:
        self.bets[bet.id] = bet

    def remove(self, bet_id: str) -> None:
        self.bets.pop(bet_id, None)

    def replace_all(self, bets: Iterable[Bet], last_sync: Optional[datetime] = None) -> None:
        self.bets = {bet.id: bet for bet in bets}
        self.last_sync = last_sync

    def as_list(self) -> List[Bet]:
        return sorted(self.bets.values(), key=lambda b: (b.event_date, b.created_at), reverse=True)

    def by_date(self, target: date) -> List[Bet]:
        return sorted(
            (bet for bet in self.bets.values() if bet.event_date == target),
            key=lambda b: b.created_at,
            reverse=True,
        )

    def by_month(self, month_key: str) -> List[Bet]:
        return sorted(
            (bet for bet in self.bets.values() if bet.event_date.strftime("%Y-%m") == month_key),
            key=lambda b: (b.event_date, b.created_at),
            reverse=True,
        )

    def months(self) -> List[str]:
        return sorted({bet.event_date.strftime("%Y-%m") for bet in self.bets.values()}, reverse=True)

    def compute_metrics(self, bets: Iterable[Bet]) -> SummaryMetrics:
        summary = SummaryMetrics()
        for bet in bets:
            summary.count += 1
            summary.stake_total += bet.stake
            ret = bet.gross_return()
            summary.return_total += ret
            net = ret - bet.stake
            summary.net += net
            if bet.outcome == "acertada":
                summary.wins += 1
            elif bet.outcome == "fallida":
                summary.losses += 1
            else:
                summary.pending += 1
        return summary

    def daily_metrics(self, target: date) -> SummaryMetrics:
        return self.compute_metrics(self.by_date(target))

    def month_metrics(self, month_key: str) -> SummaryMetrics:
        return self.compute_metrics(self.by_month(month_key))


__all__ = ["AppState", "SummaryMetrics"]
