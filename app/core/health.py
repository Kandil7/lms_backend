from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings


def check_redis_health() -> bool:
    if not settings.REDIS_URL:
        return False

    client: Redis | None = None
    try:
        client = Redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        return bool(client.ping())
    except RedisError:
        return False
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                pass
