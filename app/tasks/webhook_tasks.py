from __future__ import annotations

import hashlib
import hmac
import json
import logging
from datetime import UTC, datetime

import httpx

from app.core.config import settings
from app.tasks.celery_app import celery_app

logger = logging.getLogger("app.tasks.webhooks")


def _build_payload(event: str, data: dict) -> dict:
    return {
        "event": event,
        "timestamp": datetime.now(UTC).isoformat(),
        "data": data,
    }


def _build_headers(*, event: str, raw_body: bytes, timestamp: str) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Event": event,
        "X-Webhook-Timestamp": timestamp,
    }
    secret = (settings.WEBHOOK_SIGNING_SECRET or "").strip()
    if not secret:
        return headers

    signed_payload = f"{timestamp}.{raw_body.decode('utf-8')}".encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    headers["X-Webhook-Signature"] = f"sha256={signature}"
    return headers


@celery_app.task(
    name="app.tasks.webhook_tasks.dispatch_webhook_event",
    autoretry_for=(httpx.TimeoutException, httpx.NetworkError, httpx.TransportError),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def dispatch_webhook_event(event: str, data: dict) -> str:
    targets = [target.strip() for target in settings.WEBHOOK_TARGET_URLS if target.strip()]
    if not settings.WEBHOOKS_ENABLED:
        return "webhooks disabled"
    if not targets:
        return "no webhook targets configured"

    payload = _build_payload(event, data)
    raw_payload = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    timestamp = payload["timestamp"]
    headers = _build_headers(event=event, raw_body=raw_payload, timestamp=timestamp)

    delivered = 0
    failed = 0
    timeout = httpx.Timeout(settings.WEBHOOK_TIMEOUT_SECONDS)
    with httpx.Client(timeout=timeout) as client:
        for url in targets:
            try:
                response = client.post(url, content=raw_payload, headers=headers)
                if 200 <= response.status_code < 300:
                    delivered += 1
                else:
                    failed += 1
                    logger.warning(
                        "Webhook delivery failed event=%s target=%s status=%s body=%s",
                        event,
                        url,
                        response.status_code,
                        response.text[:500],
                    )
            except Exception as exc:
                failed += 1
                logger.warning("Webhook delivery exception event=%s target=%s error=%s", event, url, exc)

    message = f"webhook event='{event}' delivered={delivered} failed={failed} total={len(targets)}"
    if failed > 0:
        logger.warning(message)
    else:
        logger.info(message)
    return message

