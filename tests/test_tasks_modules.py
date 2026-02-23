from __future__ import annotations

import hashlib
import hmac
from contextlib import nullcontext
from types import SimpleNamespace
from uuid import uuid4

import httpx

from app.tasks import certificate_tasks, dispatcher, progress_tasks, webhook_tasks


def _inline_add(a: int, b: int) -> int:
    return a + b


def test_dispatcher_enqueue_task_success(monkeypatch) -> None:
    captured: dict = {}

    def fake_send_task(task_name: str, *, args, kwargs):
        captured["task_name"] = task_name
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(dispatcher.celery_app, "send_task", fake_send_task)
    assert dispatcher.enqueue_task("task.name", 1, 2, key="value") is True
    assert captured["task_name"] == "task.name"
    assert captured["args"] == [1, 2]
    assert captured["kwargs"] == {"key": "value"}


def test_dispatcher_enqueue_task_failure(monkeypatch) -> None:
    def fake_send_task(task_name: str, *, args, kwargs):  # pragma: no cover - branch target
        raise RuntimeError("broker down")

    monkeypatch.setattr(dispatcher.celery_app, "send_task", fake_send_task)
    assert dispatcher.enqueue_task("task.name", 1) is False


def test_dispatcher_run_task_inline_success(monkeypatch) -> None:
    monkeypatch.setitem(
        dispatcher.INLINE_TASK_MAP,
        "tests.inline.add",
        "tests.test_tasks_modules:_inline_add",
    )
    assert dispatcher.run_task_inline("tests.inline.add", 10, 5) == 15


def test_dispatcher_run_task_inline_missing_mapping() -> None:
    try:
        dispatcher.run_task_inline("tests.inline.unknown")
        assert False, "Expected ValueError for unknown inline task mapping"
    except ValueError as exc:
        assert "No inline fallback mapped" in str(exc)


def test_dispatcher_run_fallback_with_custom_callback() -> None:
    called = {"ok": False}

    def fallback() -> None:
        called["ok"] = True

    mode = dispatcher._run_fallback("some.task", fallback=fallback)
    assert mode == "inline"
    assert called["ok"] is True


def test_dispatcher_run_fallback_failure(monkeypatch) -> None:
    def fake_inline(*args, **kwargs):
        raise RuntimeError("inline failed")

    monkeypatch.setattr(dispatcher, "run_task_inline", fake_inline)
    mode = dispatcher._run_fallback("some.task")
    assert mode == "failed"


def test_dispatcher_enqueue_task_with_fallback_modes(monkeypatch) -> None:
    monkeypatch.setattr(dispatcher.settings, "TASKS_FORCE_INLINE", True)
    assert dispatcher.enqueue_task_with_fallback("any.task", fallback=lambda: None) == "inline"

    monkeypatch.setattr(dispatcher.settings, "TASKS_FORCE_INLINE", False)
    monkeypatch.setattr(dispatcher, "enqueue_task", lambda *args, **kwargs: True)
    assert dispatcher.enqueue_task_with_fallback("any.task") == "queued"

    monkeypatch.setattr(dispatcher, "enqueue_task", lambda *args, **kwargs: False)
    assert dispatcher.enqueue_task_with_fallback("any.task", fallback=lambda: None) == "inline"


def test_generate_certificate_invalid_enrollment_id() -> None:
    message = certificate_tasks.generate_certificate("not-a-uuid")
    assert message == "invalid enrollment id: not-a-uuid"


def test_generate_certificate_enrollment_not_found(monkeypatch) -> None:
    fake_db = SimpleNamespace(scalar=lambda stmt: None)
    monkeypatch.setattr(certificate_tasks, "session_scope", lambda: nullcontext(fake_db))
    message = certificate_tasks.generate_certificate(str(uuid4()))
    assert "enrollment not found" in message


def test_generate_certificate_skipped(monkeypatch) -> None:
    enrollment = SimpleNamespace(id=uuid4())
    fake_db = SimpleNamespace(scalar=lambda stmt: enrollment)
    monkeypatch.setattr(certificate_tasks, "session_scope", lambda: nullcontext(fake_db))

    class FakeCertificateService:
        def __init__(self, db):
            self.db = db

        def issue_for_enrollment(self, target):
            return None

    monkeypatch.setattr(certificate_tasks, "CertificateService", FakeCertificateService)
    message = certificate_tasks.generate_certificate(str(enrollment.id))
    assert "certificate skipped" in message


def test_generate_certificate_success(monkeypatch) -> None:
    enrollment = SimpleNamespace(id=uuid4())
    fake_db = SimpleNamespace(scalar=lambda stmt: enrollment)
    monkeypatch.setattr(certificate_tasks, "session_scope", lambda: nullcontext(fake_db))

    class FakeCertificateService:
        def __init__(self, db):
            self.db = db

        def issue_for_enrollment(self, target):
            return {"id": "cert-1"}

    monkeypatch.setattr(certificate_tasks, "CertificateService", FakeCertificateService)
    message = certificate_tasks.generate_certificate(str(enrollment.id))
    assert "certificate generated" in message


def test_recalculate_course_progress_invalid_enrollment_id() -> None:
    message = progress_tasks.recalculate_course_progress("bad")
    assert message == "invalid enrollment id: bad"


def test_recalculate_course_progress_enrollment_not_found(monkeypatch) -> None:
    fake_db = SimpleNamespace(scalar=lambda stmt: None)
    monkeypatch.setattr(progress_tasks, "session_scope", lambda: nullcontext(fake_db))
    message = progress_tasks.recalculate_course_progress(str(uuid4()))
    assert "enrollment not found" in message


def test_recalculate_course_progress_success(monkeypatch) -> None:
    enrollment = SimpleNamespace(id=uuid4())
    fake_db = SimpleNamespace(scalar=lambda stmt: enrollment)
    monkeypatch.setattr(progress_tasks, "session_scope", lambda: nullcontext(fake_db))

    called = {"seen": False}

    class FakeEnrollmentService:
        def __init__(self, db):
            self.db = db

        def recalculate_enrollment_summary(self, enrollment_id, *, commit):
            called["seen"] = True
            assert enrollment_id == enrollment.id
            assert commit is False

    monkeypatch.setattr(progress_tasks, "EnrollmentService", FakeEnrollmentService)
    message = progress_tasks.recalculate_course_progress(str(enrollment.id))
    assert "progress recalculated" in message
    assert called["seen"] is True


def test_webhook_build_headers_signature(monkeypatch) -> None:
    raw = b'{"event":"course.published"}'
    ts = "2026-01-01T00:00:00+00:00"
    monkeypatch.setattr(webhook_tasks.settings, "WEBHOOK_SIGNING_SECRET", "topsecret")
    headers = webhook_tasks._build_headers(event="course.published", raw_body=raw, timestamp=ts)
    expected = hmac.new(b"topsecret", f"{ts}.{raw.decode('utf-8')}".encode("utf-8"), hashlib.sha256).hexdigest()
    assert headers["X-Webhook-Signature"] == f"sha256={expected}"


def test_webhook_dispatch_disabled(monkeypatch) -> None:
    monkeypatch.setattr(webhook_tasks.settings, "WEBHOOKS_ENABLED", False)
    assert webhook_tasks.dispatch_webhook_event("x", {"id": 1}) == "webhooks disabled"


def test_webhook_dispatch_without_targets(monkeypatch) -> None:
    monkeypatch.setattr(webhook_tasks.settings, "WEBHOOKS_ENABLED", True)
    monkeypatch.setattr(webhook_tasks.settings, "WEBHOOK_TARGET_URLS", [])
    assert webhook_tasks.dispatch_webhook_event("x", {"id": 1}) == "no webhook targets configured"


def test_webhook_dispatch_success_and_failures(monkeypatch) -> None:
    monkeypatch.setattr(webhook_tasks.settings, "WEBHOOKS_ENABLED", True)
    monkeypatch.setattr(
        webhook_tasks.settings,
        "WEBHOOK_TARGET_URLS",
        ["https://ok.example.com", "https://bad.example.com", "https://err.example.com"],
    )
    monkeypatch.setattr(webhook_tasks.settings, "WEBHOOK_TIMEOUT_SECONDS", 2.0)
    monkeypatch.setattr(webhook_tasks.settings, "WEBHOOK_SIGNING_SECRET", "")

    class FakeClient:
        def __init__(self, timeout):
            self.timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url: str, *, content: bytes, headers: dict):
            assert headers["Content-Type"] == "application/json"
            if "ok.example.com" in url:
                return SimpleNamespace(status_code=202, text="accepted")
            if "bad.example.com" in url:
                return SimpleNamespace(status_code=500, text="boom")
            raise httpx.NetworkError("connection reset")

    monkeypatch.setattr(webhook_tasks.httpx, "Client", FakeClient)
    message = webhook_tasks.dispatch_webhook_event("course.published", {"course_id": "c1"})
    assert "delivered=1" in message
    assert "failed=2" in message
    assert "total=3" in message
