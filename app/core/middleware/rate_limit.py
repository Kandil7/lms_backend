import logging
import time
from collections import defaultdict, deque

from fastapi import status
from redis.asyncio import Redis
from redis.exceptions import RedisError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("app.rate_limit")


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
    ) -> None:
        super().__init__(app)
        self.limit = limit
        self.period_seconds = period_seconds
        self.key_prefix = key_prefix
        self.excluded_paths = excluded_paths or []

        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._redis: Redis | None = None
        self._redis_enabled = use_redis and bool(redis_url)
        self._redis_fallback_logged = False

        if self._redis_enabled and redis_url:
            self._redis = Redis.from_url(redis_url, encoding="utf-8", decode_responses=True)

    async def dispatch(self, request: Request, call_next):
        if self._is_excluded(request.url.path):
            return await call_next(request)

        client = request.client.host if request.client else "unknown"
        key = f"{self.key_prefix}:{client}:{request.url.path}"

        if self._redis_enabled and self._redis is not None:
            try:
                return await self._dispatch_with_redis(key, call_next, request)
            except Exception as exc:
                if self._should_fallback_to_memory(exc):
                    if not self._redis_fallback_logged:
                        logger.warning("Redis rate-limit fallback to in-memory mode: %s", exc)
                        self._redis_fallback_logged = True
                    self._redis_enabled = False
                    self._redis = None
                else:
                    raise

        return await self._dispatch_in_memory(key, call_next, request)

    def _is_excluded(self, path: str) -> bool:
        return any(path == excluded or path.startswith(f"{excluded}/") for excluded in self.excluded_paths)

    async def _dispatch_with_redis(self, key: str, call_next, request: Request) -> Response:
        if self._redis is None:
            return await self._dispatch_in_memory(key, call_next, request)

        count = int(await self._redis.incr(key))
        if count == 1:
            await self._redis.expire(key, self.period_seconds)

        ttl = int(await self._redis.ttl(key))
        reset_epoch = int(time.time()) + (ttl if ttl > 0 else self.period_seconds)
        remaining = max(0, self.limit - count)

        if count > self.limit:
            response = self._rate_limited_response(reset_epoch)
            self._set_rate_limit_headers(response, remaining=0, reset_epoch=reset_epoch)
            return response

        response = await call_next(request)
        self._set_rate_limit_headers(response, remaining=remaining, reset_epoch=reset_epoch)
        return response

    async def _dispatch_in_memory(self, key: str, call_next, request: Request) -> Response:
        now = time.time()
        window = self._requests[key]

        while window and now - window[0] > self.period_seconds:
            window.popleft()

        if len(window) >= self.limit:
            reset_epoch = int(window[0] + self.period_seconds) if window else int(now + self.period_seconds)
            response = self._rate_limited_response(reset_epoch)
            self._set_rate_limit_headers(response, remaining=0, reset_epoch=reset_epoch)
            return response

        window.append(now)
        remaining = max(0, self.limit - len(window))
        reset_epoch = int(window[0] + self.period_seconds)

        response = await call_next(request)
        self._set_rate_limit_headers(response, remaining=remaining, reset_epoch=reset_epoch)
        return response

    def _set_rate_limit_headers(self, response: Response, *, remaining: int, reset_epoch: int) -> None:
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_epoch)

    @staticmethod
    def _should_fallback_to_memory(exc: Exception) -> bool:
        if isinstance(exc, RedisError):
            return True
        if isinstance(exc, RuntimeError) and "Event loop is closed" in str(exc):
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
