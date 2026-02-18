import logging
import time
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext
from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.exceptions import UnauthorizedException

logger = logging.getLogger("app.security")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenType:
    ACCESS = "access"
    REFRESH = "refresh"


class AccessTokenBlacklist:
    def __init__(self, *, enabled: bool, redis_url: str | None, key_prefix: str) -> None:
        self.enabled = enabled
        self.key_prefix = key_prefix
        self._memory: dict[str, int] = {}
        self._redis_error_logged = False
        self._redis_enabled = enabled and bool(redis_url)
        self._redis: Redis | None = None

        if self._redis_enabled and redis_url:
            self._redis = Redis.from_url(redis_url, encoding="utf-8", decode_responses=True)

    def revoke(self, *, jti: str, exp_epoch: int) -> None:
        if not self.enabled:
            return

        ttl = max(0, exp_epoch - int(time.time()))
        if ttl <= 0:
            return

        if self._redis_enabled and self._redis is not None:
            try:
                self._redis.set(self._build_key(jti), "1", ex=ttl)
                return
            except RedisError as exc:
                self._fallback_to_memory(exc)

        self._memory[jti] = int(time.time()) + ttl

    def is_revoked(self, jti: str) -> bool:
        if not self.enabled:
            return False

        if self._redis_enabled and self._redis is not None:
            try:
                return bool(self._redis.exists(self._build_key(jti)))
            except RedisError as exc:
                self._fallback_to_memory(exc)

        self._cleanup_memory()
        expires_at = self._memory.get(jti)
        if not expires_at:
            return False
        if expires_at <= int(time.time()):
            self._memory.pop(jti, None)
            return False
        return True

    def _build_key(self, jti: str) -> str:
        return f"{self.key_prefix}:{jti}"

    def _cleanup_memory(self) -> None:
        now = int(time.time())
        expired_keys = [jti for jti, expires_at in self._memory.items() if expires_at <= now]
        for jti in expired_keys:
            self._memory.pop(jti, None)

    def _fallback_to_memory(self, exc: RedisError) -> None:
        if settings.ENVIRONMENT == "production" and settings.ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED:
            logger.error("Access token blacklist backend unavailable in production: %s", exc)
            raise UnauthorizedException("Token revocation service unavailable")

        if not self._redis_error_logged:
            logger.warning("Access token blacklist fallback to in-memory mode: %s", exc)
            self._redis_error_logged = True
        self._redis_enabled = False
        self._redis = None


@lru_cache(maxsize=1)
def get_access_token_blacklist() -> AccessTokenBlacklist:
    return AccessTokenBlacklist(
        enabled=settings.ACCESS_TOKEN_BLACKLIST_ENABLED,
        redis_url=settings.REDIS_URL,
        key_prefix=settings.ACCESS_TOKEN_BLACKLIST_PREFIX,
    )


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


def blacklist_access_token(token: str) -> None:
    payload = decode_token(token, expected_type=TokenType.ACCESS, check_blacklist=False)
    jti = payload.get("jti")
    exp = payload.get("exp")

    if not jti or not isinstance(exp, int | float):
        raise UnauthorizedException("Malformed token")

    get_access_token_blacklist().revoke(jti=str(jti), exp_epoch=int(exp))


def decode_token(token: str, expected_type: str | None = None, *, check_blacklist: bool = True) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as exc:
        raise UnauthorizedException("Could not validate credentials") from exc

    token_type = payload.get("typ")
    if expected_type and token_type != expected_type:
        raise UnauthorizedException("Invalid token type")

    if not payload.get("sub"):
        raise UnauthorizedException("Malformed token")

    if token_type == TokenType.ACCESS:
        jti = payload.get("jti")
        if not jti:
            raise UnauthorizedException("Malformed token")
        if check_blacklist and get_access_token_blacklist().is_revoked(str(jti)):
            raise UnauthorizedException("Token has been revoked")

    return payload
