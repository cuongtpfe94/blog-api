import logging

from redis.asyncio import Redis

from app.configs.env import get_settings

logger = logging.getLogger(__name__)


class RedisService:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = Redis.from_url(settings.redis_url, decode_responses=True)

    async def get(self, key: str) -> str | None:
        """Get value by key"""
        try:
            value = await self.client.get(key)
            if value is None:
                return None

            return str(value)
        except Exception as e:
            logger.error(f"Failed to get key: {key} - {e}")
            return None

    async def ping(self) -> bool:
        """Test Redis connection"""
        try:
            await self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            return False

    async def close(self) -> None:
        """Close Redis connection"""
        try:
            await self.client.aclose()
        except Exception as e:
            logger.error(f"Failed to close Redis connection: {e}")

    async def increment_with_ttl(self, key: str, ttl_seconds: int) -> int:
        """Increment a key with a time-to-live"""
        count = await self.client.incr(key)

        try:
            if count == 1:
                await self.client.expire(key, ttl_seconds)
            return count
        except Exception as e:
            logger.error(f"Failed to increment key: {key}")
            return 0

    async def set_with_ttl(self, key: str, value: str, ttl_seconds: int) -> None:
        """Set a key with time-to-live"""
        try:
            await self.client.set(key, value, ex=ttl_seconds)
        except Exception as e:
            logger.error(f"Failed to set key with TTL: {key} - {e}")

    async def get_ttl(self, key: str) -> int:
        """Get time-to-live of a key"""
        try:
            return await self.client.ttl(key)
        except Exception as e:
            logger.error(f"Failed to get TTL of key: {key} - {e}")
            return 0

    async def delete(self, *keys: str) -> None:
        """Delete keys"""
        try:
            await self.client.delete(*keys)
        except Exception as e:
            logger.error(f"Failed to delete keys: {keys} - {e}")
