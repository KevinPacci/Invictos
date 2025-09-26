from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from .models import TokenPayload
from .settings import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(*, subject: UUID, expires_minutes: int | None = None) -> str:
    settings = get_settings()
    expire_minutes = expires_minutes or settings.jwt_exp_minutes
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    to_encode = {"sub": str(subject), "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> TokenPayload:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Token inválido") from exc
    sub = payload.get("sub")
    if not sub:
        raise ValueError("Token sin sujeto")
    return TokenPayload(sub=UUID(sub))


__all__ = [
    "verify_password",
    "hash_password",
    "create_access_token",
    "decode_access_token",
]
