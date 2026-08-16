from app.services.email_service import EmailService
import logging

from app.schemas.request.register_request_schema import RegisterRequest
from app.schemas.request.user_create_request_schema import UserCreateRequest
from app.schemas.response.user_out_schema import UserResponse
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class RegistrationService:
    def __init__(self, db: AsyncSession, email_service: EmailService) -> None:
        self.user_service = UserService(db)
        self.auth_service = AuthService(db, email_service=email_service)

    async def register(self, payload: RegisterRequest) -> UserResponse:
        """
        Register a new user
        """
        logger.info(f"Starting registration for {payload.email}")

        user = await self.user_service.create_user(
            UserCreateRequest(
                email=payload.email,
                password=payload.password,
                display_name=payload.display_name,
            )
        )

        await self.auth_service.create_email_verification(
            user_id=user.id, email=user.email
        )

        return UserResponse.model_validate(user)
