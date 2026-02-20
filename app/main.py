import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.metrics import MetricsMiddleware, build_metrics_router, metrics_available
from app.core.middleware import (
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    ResponseEnvelopeMiddleware,
    SecurityHeadersMiddleware,
)
from app.core.middleware.rate_limit import RateLimitRule
from app.core.model_registry import load_all_models
from app.core.observability import init_sentry_for_api

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

load_all_models()
init_sentry_for_api()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.CERTIFICATES_DIR).mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/docs" if settings.API_DOCS_EFFECTIVE_ENABLED else None,
    redoc_url="/redoc" if settings.API_DOCS_EFFECTIVE_ENABLED else None,
    openapi_url="/openapi.json" if settings.API_DOCS_EFFECTIVE_ENABLED else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.TRUSTED_HOSTS)
if settings.SECURITY_HEADERS_ENABLED:
    app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)

if settings.METRICS_ENABLED and metrics_available():
    app.add_middleware(MetricsMiddleware, excluded_paths={settings.METRICS_PATH})

if settings.API_RESPONSE_ENVELOPE_ENABLED:
    app.add_middleware(
        ResponseEnvelopeMiddleware,
        success_message=settings.API_RESPONSE_SUCCESS_MESSAGE,
        excluded_paths=settings.API_RESPONSE_ENVELOPE_EXCLUDED_PATHS,
    )

rate_limit_excluded_paths = list(settings.RATE_LIMIT_EXCLUDED_PATHS)
if settings.METRICS_ENABLED and settings.METRICS_PATH not in rate_limit_excluded_paths:
    rate_limit_excluded_paths.append(settings.METRICS_PATH)

rate_limit_rules: list[RateLimitRule] = [
    RateLimitRule(
        name="auth",
        path_prefixes=settings.AUTH_RATE_LIMIT_PATHS,
        limit=settings.AUTH_RATE_LIMIT_REQUESTS_PER_MINUTE,
        period_seconds=settings.AUTH_RATE_LIMIT_WINDOW_SECONDS,
        key_mode="ip",
    ),
    RateLimitRule(
        name="upload",
        path_prefixes=settings.FILE_UPLOAD_RATE_LIMIT_PATHS,
        limit=settings.FILE_UPLOAD_RATE_LIMIT_REQUESTS_PER_HOUR,
        period_seconds=settings.FILE_UPLOAD_RATE_LIMIT_WINDOW_SECONDS,
        key_mode="user_or_ip",
    ),
]

app.add_middleware(
    RateLimitMiddleware,
    limit=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
    period_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
    use_redis=settings.RATE_LIMIT_USE_REDIS,
    redis_url=settings.REDIS_URL,
    key_prefix=settings.RATE_LIMIT_REDIS_PREFIX,
    excluded_paths=rate_limit_excluded_paths,
    custom_rules=rate_limit_rules,
)

register_exception_handlers(app)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)

if settings.METRICS_ENABLED:
    app.include_router(build_metrics_router(settings.METRICS_PATH))


@app.get("/", tags=["Root"])
def root() -> dict[str, str]:
    return {"message": "LMS Backend API"}
