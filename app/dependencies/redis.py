from functools import lru_cache

from app.services.redis_service import RedisService


@lru_cache(maxsize=1)
def get_redis_service() -> RedisService:
    """Get Redis service"""
    return RedisService()
