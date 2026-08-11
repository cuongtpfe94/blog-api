from collections.abc import AsyncGenerator

from app.dependencies.db import get_db
from app.services.registration_service import RegistrationService


async def get_registration_service() -> AsyncGenerator[RegistrationService, None]:
    """
    Dependency to get the registration service.
    """
    async for db in get_db():
        yield RegistrationService(db)
