from app.dependencies.db import get_db
from app.services.user_service import UserService
from typing import AsyncGenerator


async def get_user_service() -> AsyncGenerator[UserService, None]:
    """
    Dependency to get the user service
    """
    async for db in get_db():
        yield UserService(db)
