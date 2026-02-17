import logging
from enum import Enum

from fastapi import APIRouter

from app.core.database import check_database_health

logger = logging.getLogger(__name__)

api_router = APIRouter()


@api_router.get("/health", tags=["Health"])
def health_check() -> dict:
    return {
        "status": "ok",
        "database": "up" if check_database_health() else "down",
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
        logger.warning("Router '%s' not loaded: %s", import_path, exc)


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
