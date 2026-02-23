from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional, cast
from uuid import UUID

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)

class CacheManager:
    """Redis-based cache manager for application data."""
    
    def __init__(self):
        self.redis_client: Optional[Redis] = None
        self._memory_cache: dict[str, tuple[int, str]] = {}
        self._redis_fallback_logged = False
        self._initialize_redis()
    
    def _initialize_redis(self) -> None:
        """Initialize Redis client with connection pooling."""
        if not settings.CACHE_ENABLED:
            logger.warning("Caching is disabled in configuration")
            return
        
        try:
            self.redis_client = Redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
                socket_timeout=5,
                socket_connect_timeout=5,
            )
            # Test connection
            if self.redis_client:
                self.redis_client.ping()
                logger.info("Redis cache connected successfully")
        except RedisError as e:
            logger.warning(f"Redis cache unavailable, using in-memory fallback: {e}")
            self.redis_client = None
    
    def get(self, key: str) -> Optional[str]:
        """Get value from cache by key."""
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if isinstance(value, bytes):
                    return value.decode("utf-8")
                return cast(Optional[str], value)
            except RedisError as e:
                self._fallback_to_memory(e)
        return self._get_memory(key)
    
    def set(self, key: str, value: str, ttl_seconds: int) -> bool:
        """Set value in cache with TTL."""
        ttl = max(1, int(ttl_seconds))
        if self.redis_client:
            try:
                return bool(self.redis_client.setex(key, ttl, value))
            except RedisError as e:
                self._fallback_to_memory(e)

        self._set_memory(key, value, ttl)
        return True
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        deleted = False
        if self.redis_client:
            try:
                deleted = self.redis_client.delete(key) > 0
            except RedisError as e:
                self._fallback_to_memory(e)

        return self._memory_cache.pop(key, None) is not None or deleted

    def delete_by_prefix(self, prefix: str) -> int:
        """Delete all keys matching a prefix."""
        deleted = 0
        if self.redis_client:
            try:
                cursor = 0
                pattern = f"{prefix}*"
                while True:
                    cursor, keys = self.redis_client.scan(cursor=cursor, match=pattern, count=200)
                    if keys:
                        deleted += int(self.redis_client.delete(*keys))
                    if cursor == 0:
                        break
            except RedisError as e:
                self._fallback_to_memory(e)

        memory_keys = [key for key in self._memory_cache if key.startswith(prefix)]
        for key in memory_keys:
            self._memory_cache.pop(key, None)
        return deleted + len(memory_keys)
    
    def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value from cache."""
        cached = self.get(key)
        if cached is None:
            return None
        try:
            return json.loads(cached)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for key '{key}': {e}")
            return None
    
    def set_json(self, key: str, value: Any, ttl_seconds: int) -> bool:
        """Set JSON value in cache."""
        try:
            json_value = json.dumps(value, default=self._json_serializer)
            return self.set(key, json_value, ttl_seconds)
        except (TypeError, ValueError) as e:
            logger.error(f"JSON encode error for key '{key}': {e}")
            return False
    
    @staticmethod
    def _json_serializer(obj: Any) -> Any:
        """Custom JSON serializer for datetime objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
    
    def get_assignment_list_cache_key(self, course_id: str, skip: int, limit: int, user_id: str) -> str:
        """Generate cache key for assignment list."""
        return f"{settings.CACHE_KEY_PREFIX}:assignments:list:{course_id}:{skip}:{limit}:{user_id}"
    
    def get_assignment_cache_key(self, assignment_id: str, user_id: str) -> str:
        """Generate cache key for single assignment."""
        return f"{settings.CACHE_KEY_PREFIX}:assignments:single:{assignment_id}:{user_id}"

    def _set_memory(self, key: str, value: str, ttl_seconds: int) -> None:
        expires_at = int(time.time()) + ttl_seconds
        self._memory_cache[key] = (expires_at, value)

    def _get_memory(self, key: str) -> Optional[str]:
        cached = self._memory_cache.get(key)
        if not cached:
            return None

        expires_at, value = cached
        if expires_at <= int(time.time()):
            self._memory_cache.pop(key, None)
            return None
        return value

    def _fallback_to_memory(self, exc: RedisError) -> None:
        if not self._redis_fallback_logged:
            logger.warning(f"Cache fallback to in-memory mode: {exc}")
            self._redis_fallback_logged = True
        self.redis_client = None


# Global cache instance
cache_manager = CacheManager()
