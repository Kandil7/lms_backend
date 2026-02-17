import time
from collections import defaultdict, deque

from fastapi import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class InMemoryRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit: int = 100, period_seconds: int = 60):
        super().__init__(app)
        self.limit = limit
        self.period_seconds = period_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        client = request.client.host if request.client else "unknown"
        key = f"{client}:{request.url.path}"

        now = time.time()
        window = self._requests[key]

        while window and now - window[0] > self.period_seconds:
            window.popleft()

        if len(window) >= self.limit:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Try again later."},
            )

        window.append(now)
        return await call_next(request)
