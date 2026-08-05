from app.core.exceptions.auth_exceptions import PasswordResetTokenExpiredError
from app.core.exceptions.auth_exceptions import PasswordResetTokenUsedError
from app.core.exceptions.auth_exceptions import PasswordResetTokenInvalidError
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.configs.env import get_settings
from app.core.exceptions.auth_exceptions import (
    InvalidCredentialsError,
    UserInactiveError,
)
from app.repositories.auth_repository import AuthRepository
from app.security.password import hash_password, verify_password
from app.security.provider import get_jwt_service
from app.security.token import generate_secure_token, hash_token
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TokenPairOut:
    """
    - access_token trả trong body
    - refresh_token set trong cookie (HttpOnly) => KHÔNG đưa vào body
    """

    access_token: str
    expires_in: int
    token_type: str = "Bearer"


class AuthService:
    """
    Execute:
    - login
    - refresh
    - logout
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.auth_repository = AuthRepository(db)
        self.jwt_service = get_jwt_service()
        self.settings = get_settings()

        security_settings = self.settings.security
        if security_settings is None:
            raise RuntimeError("Security settings not found")

        self._access_ttl_minutes = security_settings.jwt.access_token_expire_minutes

    async def login(self, email: str, password: str) -> TokenPairOut | None:
        """
        Check credentials
        Generate access token
        Generate refresh token
        """
        logger.info(f"Authenticating user with email: {email}")

        user_res = await self.auth_repository.get_user_credentials_by_email(email)

        if not user_res:
            logger.error(f"User not found with email: {email}")
            raise InvalidCredentialsError(reason="invalid_credentials")

        is_valid_password = verify_password(password, user_res.hashed_password)

        if not is_valid_password:
            logger.error(f"Invalid password for email: {email}")
            raise InvalidCredentialsError(reason="invalid_credentials")

        if not user_res.is_active:
            logger.error(f"User is not active for email: {email}")
            raise UserInactiveError(reason="user_inactive")

        access_token = self.jwt_service.create_access_token(
            subject=str(user_res.id),
            extra_claims={
                "email": user_res.email,
                "display_name": user_res.display_name,
            },
        )

        return TokenPairOut(
            access_token=access_token,
            expires_in=self._access_ttl_minutes * 60,
            token_type="Bearer",
        )

    def refresh(self) -> None:
        """
        Validate refresh token
        Generate access token
        """

    def logout(self) -> None:
        """
        Invalidate refresh token
        """
        pass

    async def change_password(
        self, email: str, current_password: str, new_password: str
    ) -> None:
        """
        Change user password
        """
        logger.info(f"Changing password for user with email: {email}")
        current_user = await self.auth_repository.get_user_credentials_by_email(email)

        if not current_user:
            logger.warning(f"User not found with email: {email}")
            raise InvalidCredentialsError(reason="invalid_credentials")

        if not current_user.is_active:
            logger.warning("Inactive user tried to change password")
            raise UserInactiveError(reason="user_inactive")

        is_valid_password = verify_password(
            current_password, current_user.hashed_password
        )

        if not is_valid_password:
            logger.warning(f"Invalid current password for email: {email}")
            raise InvalidCredentialsError(reason="invalid_current_password")

        new_hashed_password = hash_password(new_password)
        await self.auth_repository.update_user_password(
            current_user.id, new_hashed_password
        )
        logger.info(f"Successfully changed password for user with email: {email}")

    async def forgot_password(self, email: str) -> None:
        """
        Create password reset token if email exists.

        Always returns None to avoid leaking whether email exists.

        Args:
            email: Email address
        """
        logger.info(f"Generating password reset token for email: {email}")
        user = await self.auth_repository.get_user_credentials_by_email(email)

        if not user:
            logger.warning(f"Forgot password for non-existent user with email: {email}")
            return

        if not user.is_active:
            logger.warning(f"Forgot password for inactive user with email: {email}")
            return

        token = generate_secure_token()
        token_hash = hash_token(token)
        expires_at = datetime.now(UTC) + timedelta(minutes=15)

        await self.auth_repository.create_password_reset_token(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        reset_link = f"http://localhost:3000/reset-password?token={token}"

        logger.info("Password reset link for %s: %s", email, reset_link)

    async def reset_password(self, *, token: str, new_password: str) -> None:
        """
        Reset user password by password reset token.

        Args:
            token: Plain password reset token from email link.
            new_password: New plain password.

        Raises:
            PasswordResetTokenInvalidError: If token does not exist.
            PasswordResetTokenExpiredError: If token has expired.
            PasswordResetTokenUsedError: If token was already used.
            UserInactiveError: If user is inactive.
        """
        logger.info("Reset password requested")

        token_hash = hash_token(token)
        reset_token = await self.auth_repository.get_password_reset_token_by_hash(token_hash)

        if reset_token is None:
            logger.warning("Invalid password reset token")
            raise PasswordResetTokenInvalidError()

        if reset_token.is_used:
            logger.warning(f"Password reset token already used: {token}")
            raise PasswordResetTokenUsedError()

        if reset_token.expires_at <= datetime.now(UTC):
            logger.warning(f"Password reset token expired: {token}")
            raise PasswordResetTokenExpiredError()

        user = await self.auth_repository.get_user_credentials_by_id(reset_token.user_id)

        if not user:
            logger.error("Password reset token points to missing user")
            raise PasswordResetTokenInvalidError()

        if not user.is_active:
            logger.error("Password reset token points to inactive user")
            raise UserInactiveError(reason="user_inactive")

        new_hashed_password = hash_password(new_password)
        await self.auth_repository.update_user_password(user.id, new_hashed_password)

        await self.auth_repository.mark_password_reset_token_used(reset_token)

        logger.info(f"Password reset successfully for user with ID: {user.id}")

