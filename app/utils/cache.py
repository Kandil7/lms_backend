from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional, TypeVar, cast
from uuid import UUID

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")

class CacheManager:
    """Redis-based cache manager for application data."""
    
    def __init__(self):
        self.redis_client: Optional[Redis] = None
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
            logger.error(f"Failed to connect to Redis cache: {e}")
            self.redis_client = None
    
    def get(self, key: str) -> Optional[str]:
        """Get value from cache by key."""
        if not self.redis_client:
            return None
        
        try:
            return self.redis_client.get(key)
        except RedisError as e:
            logger.error(f"Cache get error for key '{key}': {e}")
            return None
    
    def set(self, key: str, value: str, ttl_seconds: int) -> bool:
        """Set value in cache with TTL."""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.setex(key, ttl_seconds, value))
        except RedisError as e:
            logger.error(f"Cache set error for key '{key}': {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.redis_client:
            return False
        
        try:
            return self.redis_client.delete(key) > 0
        except RedisError as e:
            logger.error(f"Cache delete error for key '{key}': {e}")
            return False

    def delete_by_prefix(self, prefix: str) -> int:
        """Delete all keys matching a prefix."""
        if not self.redis_client:
            return 0

        deleted = 0
        try:
            cursor = 0
            pattern = f"{prefix}*"
            while True:
                cursor, keys = self.redis_client.scan(cursor=cursor, match=pattern, count=200)
                if keys:
                    deleted += int(self.redis_client.delete(*keys))
                if cursor == 0:
                    break
            return deleted
        except RedisError as e:
            logger.error(f"Cache delete_by_prefix error for prefix '{prefix}': {e}")
            return 0
    
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


# Global cache instance
cache_manager = CacheManager()
