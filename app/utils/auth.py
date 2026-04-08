import datetime
import hashlib
import uuid
from typing import Any

import bcrypt
import jwt
from passlib.hash import pbkdf2_sha256

from app.core.config import get_settings

settings = get_settings()

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def hash_password(password: str) -> str:
    return pbkdf2_sha256.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    if password_hash.startswith("$pbkdf2-sha256$"):
        return pbkdf2_sha256.verify(password, password_hash)

    if password_hash.startswith("$2"):
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except ValueError:
            return False

    return False


def _create_token(subject: str, token_type: str, expires_delta: datetime.timedelta) -> tuple[str, datetime.datetime]:
    issued_at = datetime.datetime.now(datetime.timezone.utc)
    expire = issued_at + expires_delta
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": issued_at,
        "exp": expire,
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, expire


def create_access_token(subject: str) -> str:
    token, _ = _create_token(
        subject,
        ACCESS_TOKEN_TYPE,
        datetime.timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return token


def create_refresh_token(subject: str) -> tuple[str, datetime.datetime]:
    return _create_token(
        subject,
        REFRESH_TOKEN_TYPE,
        datetime.timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str, expected_type: str | None = None) -> dict[str, Any]:
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    token_type = payload.get("type")
    if expected_type and token_type != expected_type:
        raise jwt.InvalidTokenError("Invalid token type")
    return payload


def decode_access_token(token: str) -> dict[str, Any]:
    return decode_token(token, expected_type=ACCESS_TOKEN_TYPE)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
