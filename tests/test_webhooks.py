from app.core.webhooks import emit_webhook_event


def test_emit_webhook_event_disabled(monkeypatch) -> None:
    monkeypatch.setattr("app.core.webhooks.settings.WEBHOOKS_ENABLED", False)
    result = emit_webhook_event("enrollment.created", {"enrollment_id": "x"})
    assert result == "disabled"


def test_emit_webhook_event_requires_targets(monkeypatch) -> None:
    monkeypatch.setattr("app.core.webhooks.settings.WEBHOOKS_ENABLED", True)
    monkeypatch.setattr("app.core.webhooks.settings.WEBHOOK_TARGET_URLS", [])
    result = emit_webhook_event("enrollment.created", {"enrollment_id": "x"})
    assert result == "no_targets"


def test_emit_webhook_event_enqueues_task(monkeypatch) -> None:
    captured: dict = {}

    def fake_enqueue(task_name: str, *args, **kwargs):
        captured["task_name"] = task_name
        captured["kwargs"] = kwargs
        return "queued"

    monkeypatch.setattr("app.core.webhooks.settings.WEBHOOKS_ENABLED", True)
    monkeypatch.setattr("app.core.webhooks.settings.WEBHOOK_TARGET_URLS", ["https://example.com/webhook"])
    monkeypatch.setattr("app.core.webhooks.enqueue_task_with_fallback", fake_enqueue)

    result = emit_webhook_event("course.published", {"course_id": "abc"})

    assert result == "queued"
    assert captured["task_name"] == "app.tasks.webhook_tasks.dispatch_webhook_event"
    assert captured["kwargs"]["event"] == "course.published"
    assert captured["kwargs"]["data"] == {"course_id": "abc"}

