from datetime import UTC, datetime, timedelta
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import UnauthorizedException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenType:
    ACCESS = "access"
    REFRESH = "refresh"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _create_token(payload: dict, expires_delta: timedelta, token_type: str) -> str:
    to_encode = payload.copy()
    now = datetime.now(UTC)
    to_encode.update(
        {
            "jti": str(uuid4()),
            "typ": token_type,
            "iat": now,
            "exp": now + expires_delta,
        }
    )
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(subject: str, role: str) -> str:
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token({"sub": subject, "role": role}, expires_delta, TokenType.ACCESS)


def create_refresh_token(subject: str) -> str:
    expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_token({"sub": subject}, expires_delta, TokenType.REFRESH)


def decode_token(token: str, expected_type: str | None = None) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as exc:
        raise UnauthorizedException("Could not validate credentials") from exc

    token_type = payload.get("typ")
    if expected_type and token_type != expected_type:
        raise UnauthorizedException("Invalid token type")

    if not payload.get("sub"):
        raise UnauthorizedException("Malformed token")

    return payload
