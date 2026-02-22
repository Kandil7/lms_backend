from __future__ import annotations

import logging

from app.core.config import settings

logger = logging.getLogger("app.observability")

_api_sentry_initialized = False
_celery_sentry_initialized = False


def init_sentry_for_api() -> None:
    global _api_sentry_initialized
    if _api_sentry_initialized:
        return
    if not settings.SENTRY_DSN:
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT_EFFECTIVE,
            release=settings.SENTRY_RELEASE or settings.VERSION,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
            send_default_pii=settings.SENTRY_SEND_PII,
            integrations=[FastApiIntegration(), StarletteIntegration()],
        )
        _api_sentry_initialized = True
        logger.info("Sentry initialized for API (environment=%s)", settings.SENTRY_ENVIRONMENT_EFFECTIVE)
    except Exception:
        logger.exception("Failed to initialize Sentry for API")


def init_sentry_for_celery() -> None:
    global _celery_sentry_initialized
    if _celery_sentry_initialized:
        return
    if not settings.SENTRY_DSN or not settings.SENTRY_ENABLE_FOR_CELERY:
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.celery import CeleryIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT_EFFECTIVE,
            release=settings.SENTRY_RELEASE or settings.VERSION,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
            send_default_pii=settings.SENTRY_SEND_PII,
            integrations=[CeleryIntegration(monitor_beat_tasks=True)],
        )
        _celery_sentry_initialized = True
        logger.info("Sentry initialized for Celery (environment=%s)", settings.SENTRY_ENVIRONMENT_EFFECTIVE)
    except Exception:
        logger.exception("Failed to initialize Sentry for Celery")
