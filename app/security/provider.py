from functools import lru_cache

from app.configs.env import get_settings
from app.security.jwt import JWTService


@lru_cache
def get_jwt_service() -> JWTService:
    settings = get_settings()
    if settings.security is None:
        raise RuntimeError("Security settings not initialized")
    return JWTService(settings.security.jwt)
