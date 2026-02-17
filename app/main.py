import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.middleware import RateLimitMiddleware, RequestLoggingMiddleware

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)


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
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    limit=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
    period_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
    use_redis=settings.RATE_LIMIT_USE_REDIS,
    redis_url=settings.REDIS_URL,
    key_prefix=settings.RATE_LIMIT_REDIS_PREFIX,
    excluded_paths=settings.RATE_LIMIT_EXCLUDED_PATHS,
)

register_exception_handlers(app)

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR, check_dir=False), name="uploads")
app.mount(
    "/certificates-static",
    StaticFiles(directory=settings.CERTIFICATES_DIR, check_dir=False),
    name="certificates-static",
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
def root() -> dict[str, str]:
    return {"message": "LMS Backend API"}
