import json
import logging
import time
from functools import lru_cache
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger("app.cache")


class AppCache:
    def __init__(self, *, enabled: bool, redis_url: str | None, key_prefix: str, default_ttl_seconds: int) -> None:
        self.enabled = enabled
        self.key_prefix = key_prefix
        self.default_ttl_seconds = max(1, default_ttl_seconds)
        self._memory: dict[str, tuple[int, str]] = {}
        self._redis_error_logged = False
        self._redis_enabled = enabled and bool(redis_url)
        self._redis: Redis | None = None

        if self._redis_enabled and redis_url:
            self._redis = Redis.from_url(redis_url, encoding="utf-8", decode_responses=True)

    def get_json(self, key: str) -> Any | None:
        if not self.enabled:
            return None

        full_key = self._build_key(key)
        payload: str | None = None

        if self._redis_enabled and self._redis is not None:
            try:
                payload = self._redis.get(full_key)
            except RedisError as exc:
                self._fallback_to_memory(exc)

        if payload is None:
            payload = self._get_memory(full_key)

        if payload is None:
            return None

        try:
            return json.loads(payload)
        except Exception:
            return None

    def set_json(self, key: str, value: Any, *, ttl_seconds: int | None = None) -> None:
        if not self.enabled:
            return

        ttl = max(1, ttl_seconds or self.default_ttl_seconds)
        full_key = self._build_key(key)
        payload = json.dumps(value)

        if self._redis_enabled and self._redis is not None:
            try:
                self._redis.set(full_key, payload, ex=ttl)
                return
            except RedisError as exc:
                self._fallback_to_memory(exc)

        self._set_memory(full_key, payload, ttl)

    def delete_by_prefix(self, prefix: str) -> None:
        if not self.enabled:
            return

        full_prefix = self._build_key(prefix)

        if self._redis_enabled and self._redis is not None:
            try:
                keys = list(self._redis.scan_iter(match=f"{full_prefix}*"))
                if keys:
                    self._redis.delete(*keys)
            except RedisError as exc:
                self._fallback_to_memory(exc)

        keys_to_delete = [key for key in self._memory if key.startswith(full_prefix)]
        for key in keys_to_delete:
            self._memory.pop(key, None)

    def _build_key(self, key: str) -> str:
        return f"{self.key_prefix}:{key}"

    def _set_memory(self, key: str, payload: str, ttl_seconds: int) -> None:
        expires_at = int(time.time()) + ttl_seconds
        self._memory[key] = (expires_at, payload)

    def _get_memory(self, key: str) -> str | None:
        item = self._memory.get(key)
        if not item:
            return None

        expires_at, payload = item
        if expires_at <= int(time.time()):
            self._memory.pop(key, None)
            return None
        return payload

    def _fallback_to_memory(self, exc: RedisError) -> None:
        if not self._redis_error_logged:
            logger.warning("Cache fallback to in-memory mode: %s", exc)
            self._redis_error_logged = True
        self._redis_enabled = False
        self._redis = None


@lru_cache(maxsize=1)
def get_app_cache() -> AppCache:
    return AppCache(
        enabled=settings.CACHE_ENABLED,
        redis_url=settings.REDIS_URL,
        key_prefix=settings.CACHE_KEY_PREFIX,
        default_ttl_seconds=settings.CACHE_DEFAULT_TTL_SECONDS,
    )
