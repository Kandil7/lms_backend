import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock

from app.core.exceptions import UnauthorizedException
from app.core.security import TokenType, decode_token

from fastapi import status
from redis.asyncio import Redis
from redis.exceptions import RedisError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("app.rate_limit")

# Maximum number of rate limit keys to keep in memory
MAX_IN_MEMORY_KEYS = 10000
# Cleanup interval in seconds (every 5 minutes)
CLEANUP_INTERVAL_SECONDS = 300


@dataclass(slots=True)
class RateLimitRule:
    name: str
    path_prefixes: list[str]
    limit: int
    period_seconds: int
    key_mode: str = "ip"


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        limit: int = 100,
        period_seconds: int = 60,
        use_redis: bool = True,
        redis_url: str | None = None,
        key_prefix: str = "ratelimit",
        excluded_paths: list[str] | None = None,
        custom_rules: list[RateLimitRule] | None = None,
    ) -> None:
        super().__init__(app)
        self.limit = limit
        self.period_seconds = period_seconds
        self.key_prefix = key_prefix
        self.excluded_paths = excluded_paths or []
        self.custom_rules = custom_rules or []

        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()
        self._last_cleanup_time = time.time()
        self._redis: Redis | None = None
        self._redis_enabled = use_redis and bool(redis_url)
        self._redis_fallback_logged = False

        if self._redis_enabled and redis_url:
            self._redis = Redis.from_url(
                redis_url, encoding="utf-8", decode_responses=True
            )

    async def dispatch(self, request: Request, call_next):
        if self._is_excluded(request.url.path):
            return await call_next(request)

        rule = self._resolve_rule(request.url.path)
        limit = rule.limit if rule else self.limit
        period_seconds = rule.period_seconds if rule else self.period_seconds
        rule_key_prefix = f"{self.key_prefix}:{rule.name}" if rule else self.key_prefix
        key_mode = rule.key_mode if rule else "ip"
        client_key = self._build_client_key(request, key_mode)
        key = f"{rule_key_prefix}:{client_key}:{request.url.path}"

        if self._redis_enabled and self._redis is not None:
            try:
                return await self._dispatch_with_redis(
                    key,
                    call_next,
                    request,
                    limit=limit,
                    period_seconds=period_seconds,
                )
            except Exception as exc:
                if self._should_fallback_to_memory(exc):
                    if not self._redis_fallback_logged:
                        logger.warning(
                            "Redis rate-limit fallback to in-memory mode: %s", exc
                        )
                        self._redis_fallback_logged = True
                    self._redis_enabled = False
                    self._redis = None
                else:
                    raise

        return await self._dispatch_in_memory(
            key,
            call_next,
            request,
            limit=limit,
            period_seconds=period_seconds,
        )

    def _is_excluded(self, path: str) -> bool:
        return any(
            path == excluded or path.startswith(f"{excluded}/")
            for excluded in self.excluded_paths
        )

    async def _dispatch_with_redis(
        self,
        key: str,
        call_next,
        request: Request,
        *,
        limit: int,
        period_seconds: int,
    ) -> Response:
        if self._redis is None:
            return await self._dispatch_in_memory(
                key,
                call_next,
                request,
                limit=limit,
                period_seconds=period_seconds,
            )

        count = int(await self._redis.incr(key))
        if count == 1:
            await self._redis.expire(key, period_seconds)

        ttl = int(await self._redis.ttl(key))
        reset_epoch = int(time.time()) + (ttl if ttl > 0 else period_seconds)
        remaining = max(0, limit - count)

        if count > limit:
            response = self._rate_limited_response(reset_epoch)
            self._set_rate_limit_headers(
                response, limit=limit, remaining=0, reset_epoch=reset_epoch
            )
            return response

        response = await call_next(request)
        self._set_rate_limit_headers(
            response, limit=limit, remaining=remaining, reset_epoch=reset_epoch
        )
        return response

    async def _dispatch_in_memory(
        self,
        key: str,
        call_next,
        request: Request,
        *,
        limit: int,
        period_seconds: int,
    ) -> Response:
        now = time.time()

        # Periodic cleanup of expired keys to prevent memory leak
        self._maybe_cleanup(now)

        window = self._requests[key]

        while window and now - window[0] > period_seconds:
            window.popleft()

        if len(window) >= limit:
            reset_epoch = (
                int(window[0] + period_seconds) if window else int(now + period_seconds)
            )
            response = self._rate_limited_response(reset_epoch)
            self._set_rate_limit_headers(
                response, limit=limit, remaining=0, reset_epoch=reset_epoch
            )
            return response

        window.append(now)
        remaining = max(0, limit - len(window))
        reset_epoch = int(window[0] + period_seconds)

        response = await call_next(request)
        self._set_rate_limit_headers(
            response, limit=limit, remaining=remaining, reset_epoch=reset_epoch
        )
        return response

    def _maybe_cleanup(self, now: float) -> None:
        """Clean up expired rate limit keys if enough time has passed."""
        if now - self._last_cleanup_time < CLEANUP_INTERVAL_SECONDS:
            return

        with self._lock:
            # Double-check after acquiring lock
            if now - self._last_cleanup_time < CLEANUP_INTERVAL_SECONDS:
                return

            self._last_cleanup_time = now

            # Clean up expired entries
            expired_keys = []
            for key, window in self._requests.items():
                # Remove expired timestamps from the window
                while window and now - window[0] > self.period_seconds:
                    window.popleft()
                # If window is empty, mark key for deletion
                if not window:
                    expired_keys.append(key)

            for key in expired_keys:
                self._requests.pop(key, None)

            # Log if we had to clean up
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired rate limit keys")

            # If still too many keys, log warning
            if len(self._requests) > MAX_IN_MEMORY_KEYS:
                logger.warning(
                    f"Rate limit in-memory store has {len(self._requests)} keys, "
                    f"consider using Redis for rate limiting"
                )

    def _set_rate_limit_headers(
        self, response: Response, *, limit: int, remaining: int, reset_epoch: int
    ) -> None:
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_epoch)

    def _resolve_rule(self, path: str) -> RateLimitRule | None:
        for rule in self.custom_rules:
            if any(
                path == prefix or path.startswith(f"{prefix}/")
                for prefix in rule.path_prefixes
            ):
                return rule
        return None

    def _build_client_key(self, request: Request, key_mode: str) -> str:
        if key_mode == "user_or_ip":
            user_id = self._extract_user_id(request)
            if user_id:
                return f"user:{user_id}"
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    @staticmethod
    def _extract_user_id(request: Request) -> str | None:
        authorization = request.headers.get("Authorization", "").strip()
        if not authorization.lower().startswith("bearer "):
            return None
        token = authorization[7:].strip()
        if not token:
            return None
        try:
            payload = decode_token(
                token, expected_type=TokenType.ACCESS, check_blacklist=False
            )
        except UnauthorizedException:
            return None
        except Exception:
            return None
        sub = payload.get("sub")
        if not isinstance(sub, str) or not sub:
            return None
        return sub

    @staticmethod
    def _should_fallback_to_memory(exc: Exception) -> bool:
        if isinstance(exc, RedisError):
            return True
        if isinstance(exc, RuntimeError):
            message = str(exc)
            if "Event loop is closed" in message or "attached to a different loop" in message:
                return True
        return False

    @staticmethod
    def _rate_limited_response(reset_epoch: int) -> JSONResponse:
        retry_after = max(1, int(reset_epoch - time.time()))
        response = JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded. Try again later."},
        )
        response.headers["Retry-After"] = str(retry_after)
        return response
