from __future__ import annotations

from datetime import date

from sqlmodel import delete

from .db import init_db, session_scope
from .models import Bet, BetOutcome, BetType, ParlayLeg, utcnow


def seed_demo_data() -> None:
    init_db()
    with session_scope() as session:
        session.exec(delete(ParlayLeg))
        session.exec(delete(Bet))

        sample = [
            Bet(
                event_date=date(2025, 9, 24),
                type=BetType.SINGLE,
                detail="Serie A - Inter vs Milan, over 2.5 goles",
                stake=80,
                odds=1.92,
                cashout=None,
                outcome=BetOutcome.WIN,
            ),
            Bet(
                event_date=date(2025, 9, 24),
                type=BetType.PARLAY,
                detail="Parlay liga MX sábado",
                stake=40,
                odds=3.25,
                cashout=None,
                outcome=BetOutcome.PENDING,
                legs=[
                    ParlayLeg(detail="America gana vs Cruz Azul", odds=1.55),
                    ParlayLeg(detail="Monterrey +1.5 goles", odds=1.75),
                    ParlayLeg(detail="Toluca doble oportunidad", odds=1.2),
                ],
            ),
            Bet(
                event_date=date(2025, 9, 23),
                type=BetType.SINGLE,
                detail="NFL - Ravens ML vs Bengals",
                stake=100,
                odds=1.68,
                cashout=0,
                outcome=BetOutcome.LOSS,
            ),
            Bet(
                event_date=date(2025, 8, 18),
                type=BetType.SINGLE,
                detail="Premier League - Arsenal gana y ambos anotan",
                stake=60,
                odds=3.1,
                cashout=186,
                outcome=BetOutcome.WIN,
            ),
            Bet(
                event_date=date(2025, 8, 22),
                type=BetType.PARLAY,
                detail="Parlay MLS viernes",
                stake=35,
                odds=4.6,
                cashout=None,
                outcome=BetOutcome.LOSS,
                legs=[
                    ParlayLeg(detail="LAFC + over 1.5 goles", odds=1.9),
                    ParlayLeg(detail="Inter Miami gana", odds=1.65),
                    ParlayLeg(detail="Atlanta United +0.5", odds=1.45),
                ],
            ),
        ]

        now = utcnow()
        for bet in sample:
            bet.created_at = now
            bet.updated_at = now
            session.add(bet)


if __name__ == "__main__":
    seed_demo_data()
    print("Datos de ejemplo cargados")
