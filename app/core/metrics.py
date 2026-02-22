from __future__ import annotations

from time import perf_counter
from typing import Any

from fastapi import APIRouter, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"
_PROMETHEUS_AVAILABLE = False

HTTP_REQUESTS_TOTAL: Any | None = None
HTTP_REQUEST_DURATION_SECONDS: Any | None = None
HTTP_REQUESTS_IN_PROGRESS: Any | None = None


def generate_latest() -> bytes:
    return b""


try:
    from prometheus_client import CONTENT_TYPE_LATEST as _CONTENT_TYPE_LATEST
    from prometheus_client import Counter as _Counter
    from prometheus_client import Gauge as _Gauge
    from prometheus_client import Histogram as _Histogram
    from prometheus_client import generate_latest as _generate_latest

    CONTENT_TYPE_LATEST = _CONTENT_TYPE_LATEST
    HTTP_REQUESTS_TOTAL = _Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "path", "status"],
    )
    HTTP_REQUEST_DURATION_SECONDS = _Histogram(
        "http_request_duration_seconds",
        "HTTP request latency in seconds",
        ["method", "path"],
    )
    HTTP_REQUESTS_IN_PROGRESS = _Gauge(
        "http_requests_in_progress",
        "In-progress HTTP requests",
    )
    generate_latest = _generate_latest
    _PROMETHEUS_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency runtime guard
    pass


def metrics_available() -> bool:
    return _PROMETHEUS_AVAILABLE


def build_metrics_router(path: str) -> APIRouter:
    router = APIRouter(include_in_schema=False)

    @router.get(path)
    def metrics_endpoint() -> Response:
        if not _PROMETHEUS_AVAILABLE:
            return Response(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content="metrics backend unavailable",
                media_type="text/plain",
            )
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return router


class MetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, excluded_paths: set[str] | None = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or set()

    async def dispatch(self, request: Request, call_next):
        if not _PROMETHEUS_AVAILABLE:
            return await call_next(request)
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        method = request.method
        status_code = 500
        started_at = perf_counter()

        assert HTTP_REQUESTS_IN_PROGRESS is not None
        assert HTTP_REQUESTS_TOTAL is not None
        assert HTTP_REQUEST_DURATION_SECONDS is not None

        HTTP_REQUESTS_IN_PROGRESS.inc()
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration = perf_counter() - started_at
            path = _resolve_path_template(request)
            HTTP_REQUESTS_IN_PROGRESS.dec()
            HTTP_REQUESTS_TOTAL.labels(method=method, path=path, status=str(status_code)).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(method=method, path=path).observe(duration)


def _resolve_path_template(request: Request) -> str:
    route = request.scope.get("route")
    route_path = getattr(route, "path", None)
    if isinstance(route_path, str) and route_path:
        return route_path
    return request.url.path

