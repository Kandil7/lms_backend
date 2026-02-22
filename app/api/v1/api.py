import logging
from enum import Enum

from fastapi import APIRouter, Response, status

from app.core.config import settings
from app.core.database import check_database_health
from app.core.health import check_redis_health

logger = logging.getLogger(__name__)

api_router = APIRouter()


@api_router.get("/health", tags=["Health"])
def health_check() -> dict:
    return {"status": "ok"}


@api_router.get("/ready", tags=["Health"])
def readiness_check(response: Response) -> dict:
    db_up = check_database_health()
    redis_up = check_redis_health()
    if not db_up or not redis_up:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "ok" if db_up and redis_up else "degraded",
        "database": "up" if db_up else "down",
        "redis": "up" if redis_up else "down",
    }


def _safe_include(
    router: APIRouter,
    import_path: str,
    *,
    prefix: str = "",
    tags: list[str | Enum] | None = None,
) -> None:
    module_name, attr_name = import_path.rsplit(":", 1)

    try:
        module = __import__(module_name, fromlist=[attr_name])
        include_router = getattr(module, attr_name)
        router.include_router(include_router, prefix=prefix, tags=tags)
    except Exception as exc:  # pragma: no cover - startup best effort
        if settings.STRICT_ROUTER_IMPORTS_EFFECTIVE:
            logger.exception("Router '%s' failed during startup and strict mode is enabled.", import_path)
            raise RuntimeError(f"Router '{import_path}' failed to load") from exc
        logger.warning("Router '%s' not loaded: %s", import_path, exc)


# Use cookie-based auth router in production for enhanced security
if settings.ENVIRONMENT == "production":
    _safe_include(api_router, "app.modules.auth.router_cookie:router")
else:
    _safe_include(api_router, "app.modules.auth.router:router")
_safe_include(api_router, "app.modules.users.router:router")
_safe_include(api_router, "app.modules.courses.routers.course_router:router")
_safe_include(api_router, "app.modules.courses.routers.lesson_router:router")
_safe_include(api_router, "app.modules.enrollments.router:router")
_safe_include(api_router, "app.modules.quizzes.routers.quiz_router:router")
_safe_include(api_router, "app.modules.quizzes.routers.question_router:router")
_safe_include(api_router, "app.modules.quizzes.routers.attempt_router:router")
_safe_include(api_router, "app.modules.analytics.router:router")
_safe_include(api_router, "app.modules.files.router:router")
_safe_include(api_router, "app.modules.certificates.router:router")
