from pydantic import BaseModel


class RedisHealthResponse(BaseModel):
    """Response schema for Redis health check"""

    status: str
    redis: str
