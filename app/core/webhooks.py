from __future__ import annotations

from collections.abc import Mapping

from app.core.config import settings
from app.tasks.dispatcher import enqueue_task_with_fallback


def emit_webhook_event(event: str, data: Mapping[str, object]) -> str:
    if not settings.WEBHOOKS_ENABLED:
        return "disabled"
    if not settings.WEBHOOK_TARGET_URLS:
        return "no_targets"
    return enqueue_task_with_fallback(
        "app.tasks.webhook_tasks.dispatch_webhook_event",
        event=event,
        data=dict(data),
    )

