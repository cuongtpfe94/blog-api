from app.dependencies.email import get_email_service
from collections.abc import AsyncGenerator

from app.dependencies.db import get_db
from app.services.registration_service import RegistrationService


async def get_registration_service() -> AsyncGenerator[RegistrationService, None]:
    """
    Dependency to get the registration service.
    """
    email_service = get_email_service()
    async for db in get_db():
        yield RegistrationService(db, email_service=email_service)
