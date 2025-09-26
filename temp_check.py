from backend.db import session_scope
from backend import crud
from backend.models import BetRead

with session_scope() as session:
    bets = crud.list_bets(session)
    print("bets fetched", len(bets))
    if bets:
        print(BetRead.model_validate(bets[0]))

