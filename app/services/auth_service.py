from app.core.exceptions.auth_exceptions import TokenInvalidError
from app.dependencies import email
from app.core.exceptions.auth_exceptions import TooManyEmailRequestsError
from app.core.exceptions import auth_exceptions
from app.core.exceptions.auth_exceptions import TooManyLoginAttemptsError
from app.services.redis_service import RedisService
from app.services.email_service import EmailService
from app.core.exceptions.auth_exceptions import EmailNotVerifiedError
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.configs.env import get_settings
from app.core.exceptions.auth_exceptions import (
    EmailVerificationTokenExpiredError,
    EmailVerificationTokenInvalidError,
    EmailVerificationTokenUsedError,
    InvalidCredentialsError,
    PasswordResetTokenExpiredError,
    PasswordResetTokenInvalidError,
    PasswordResetTokenUsedError,
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
    refresh_token: str
    expires_in: int
    token_type: str = "Bearer"


class AuthService:
    """
    Execute:
    - login
    - refresh
    - logout
    """

    def __init__(
        self, db: AsyncSession, email_service: EmailService, redis_service: RedisService
    ) -> None:
        self.db = db
        self.auth_repository = AuthRepository(db)
        self.jwt_service = get_jwt_service()
        self.email_service = email_service or EmailService()
        self.redis_service = redis_service or RedisService()
        self.settings = get_settings()

        security_settings = self.settings.security
        if security_settings is None:
            raise RuntimeError("Security settings not found")

        self._access_ttl_minutes = security_settings.jwt.access_token_expire_minutes

    async def login(
        self, email: str, password: str, client_ip: str
    ) -> TokenPairOut | None:
        """
        Check credentials
        Generate access token
        Generate refresh token
        """
        logger.info(f"Authenticating user with email: {email}")

        await self._ensure_login_is_not_blocked(email=email, client_ip=client_ip)

        user_res = await self.auth_repository.get_user_credentials_by_email(email)

        if not user_res:
            logger.error(f"User not found with email: {email}")
            await self._record_failed_login(email=email, client_ip=client_ip)
            raise InvalidCredentialsError(reason="invalid_credentials")

        is_valid_password = verify_password(password, user_res.hashed_password)

        if not is_valid_password:
            logger.error(f"Invalid password for email: {email}")
            await self._record_failed_login(email=email, client_ip=client_ip)
            raise InvalidCredentialsError(reason="invalid_credentials")

        if not user_res.is_active:
            logger.error(f"User is not active for email: {email}")
            raise UserInactiveError(reason="user_inactive")

        if not user_res.is_verified:
            logger.warning("Login block because email is not verified")
            raise EmailNotVerifiedError()

        access_token = self.jwt_service.create_access_token(
            subject=str(user_res.id),
            extra_claims={
                "email": user_res.email,
                "display_name": user_res.display_name,
            },
        )

        refresh_token = self.jwt_service.create_refresh_token(
            subject=str(user_res.id),
            extra_claims={
                "email": user_res.email,
                "display_name": user_res.display_name,
                "token_version": user_res.token_version
            },
        )

        await self._clear_failed_login(email=email, client_ip=client_ip)

        return TokenPairOut(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self._access_ttl_minutes * 60,
            token_type="Bearer",
        )

    async def refresh(self, refresh_token: str) -> TokenPairOut:
        """
        Create a new access token from a valid refresh token.
        """
        logger.info("Refreshing access token")

        payload = self.jwt_service.decode_refresh_token(refresh_token)

        subject = payload.get("sub")
        jti = payload.get("jti")
        token_version = payload.get("token_version")

        if subject is None or jti is None or token_version is None:
            raise TokenInvalidError(token_type="refresh")

        await self._ensure_refresh_token_is_not_blacklisted(str(jti))

        try:
            user_id = int(subject)
        except (TypeError, ValueError) as err:
            raise TokenInvalidError(token_type="refresh") from err

        user = await self.auth_repository.get_user_credentials_by_id(user_id)

        if user is None:
            raise TokenInvalidError(token_type="refresh")

        if user.token_version != token_version:
            raise TokenInvalidError(token_type="refresh")

        if not user.is_active:
            raise UserInactiveError(token_type="refresh", reason="user_inactive")

        if not user.is_verified:
            raise EmailNotVerifiedError()

        access_token = self.jwt_service.create_access_token(
            subject=str(user.id),
            extra_claims={
                "email": user.email,
                "display_name": user.display_name,
            },
        )

        return TokenPairOut(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self._access_ttl_minutes * 60,
            token_type="Bearer",
        )

    async def logout(self, refresh_token: str) -> None:
        """
        Logout current device by blacklisting current refresh token.
        """
        logger.info("Logging out current device")

        payload = self.jwt_service.decode_refresh_token(refresh_token)

        jti = payload.get("jti")
        exp = payload.get("exp")

        if jti is None or exp is None:
            raise TokenInvalidError(token_type="refresh")

        await self._blacklist_refresh_token(jti=str(jti), exp=int(exp))

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

    async def forgot_password(self, email: str, client_ip: str) -> None:
        """
        Create password reset token if email exists.

        Always returns None to avoid leaking whether email exists.

        Args:
            email: Email address
        """
        logger.info(f"Generating password reset token for email: {email}")

        await self._ensure_email_action_is_not_blocked(
            action="forgot-password",
            email=email,
            client_ip=client_ip,
        )

        await self._record_email_action(
            action="forgot-password",
            email=email,
            client_ip=client_ip,
        )

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

        reset_link = f"{self.settings.frontend_url}/reset-password?token={token}"

        await self.email_service.send_password_reset_email(
            to_email=email, reset_link=reset_link
        )

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
        reset_token = await self.auth_repository.get_password_reset_token_by_hash(
            token_hash
        )

        if reset_token is None:
            logger.warning("Invalid password reset token")
            raise PasswordResetTokenInvalidError()

        if reset_token.is_used:
            logger.warning(f"Password reset token already used: {token}")
            raise PasswordResetTokenUsedError()

        if reset_token.expires_at <= datetime.now(UTC):
            logger.warning(f"Password reset token expired: {token}")
            raise PasswordResetTokenExpiredError()

        user = await self.auth_repository.get_user_credentials_by_id(
            reset_token.user_id
        )

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

    async def create_email_verification(self, *, user_id: int, email: str) -> None:
        logger.info(f"Generating email verification token for email: {email}")

        token = generate_secure_token()
        token_hash = hash_token(token)
        expires_at = datetime.now(UTC) + timedelta(hours=24)

        await self.auth_repository.create_email_verification_token(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        verification_link = f"{self.settings.frontend_url}/verify-email?token={token}"

        await self.email_service.send_email_verification_email(
            to_email=email,
            verification_link=verification_link,
        )

    async def verify_email(self, *, token: str) -> None:
        """
        Verify user email by email verification token
        """

        logger.info("Email verification requested")

        token_hash = hash_token(token)
        email_verification_token = (
            await self.auth_repository.get_email_verification_token_by_hash(token_hash)
        )

        if email_verification_token is None:
            logger.warning("Invalid email verification token")
            raise EmailVerificationTokenInvalidError()

        if email_verification_token.is_used:
            logger.warning(f"Email verification token already used: {token}")
            raise EmailVerificationTokenUsedError()

        if email_verification_token.expires_at <= datetime.now(UTC):
            logger.warning(f"Email verification token expired: {token}")
            raise EmailVerificationTokenExpiredError()

        user = await self.auth_repository.get_user_credentials_by_id(
            email_verification_token.user_id
        )

        if not user:
            logger.error("Email verification token points to missing user")
            raise EmailVerificationTokenInvalidError()

        if not user.is_active:
            logger.error("Email verification token points to inactive user")
            raise UserInactiveError(reason="user_inactive")

        await self.auth_repository.mark_email_verification_token_used(
            email_verification_token
        )
        await self.auth_repository.update_user_verified_status(user_id=user.id)

        logger.info(f"Email verification successfully for user with ID: {user.id}")

    async def resend_verification_email(self, *, email: str, client_ip: str) -> None:
        """
        Generate a new email verification token and send it to the user.

        Always returns None to avoid leaking whether the email exists.
        """
        await self._ensure_email_action_is_not_blocked(
            action="resend-verification",
            email=email,
            client_ip=client_ip,
        )

        await self._record_email_action(
            action="resend-verification",
            email=email,
            client_ip=client_ip,
        )

        logger.info("Resend verification email request for email: %s", email)

        user = await self.auth_repository.get_user_credentials_by_email(email)

        if user is None:
            logger.warning(
                "Resend verification email for non-existent user with email: %s", email
            )
            return

        if not user.is_active:
            logger.warning("Resend verification email for inactive user")
            return

        if user.is_verified:
            logger.warning("Resend verification email for verified user")
            return

        await self.create_email_verification(user_id=user.id, email=email)

    def _login_email_fail_key(self, email: str) -> str:
        email_key = hash_token(email.lower().strip())
        return f"auth:login:fail:email:{email_key}"

    def _login_email_block_key(self, email: str) -> str:
        email_key = hash_token(email.lower().strip())
        return f"auth:login:block:email:{email_key}"

    def _login_ip_fail_key(self, ip_address: str) -> str:
        return f"auth:login:fail:ip:{ip_address}"

    def _login_ip_block_key(self, ip_address: str) -> str:
        return f"auth:login:block:ip:{ip_address}"

    async def _ensure_login_is_not_blocked(
        self,
        *,
        email: str,
        client_ip: str,
    ) -> None:
        """
        Raise rate limit errors if login is blocked.

        Args:
            email: User email.
            client_ip: Client IP address.

        Raises:
            LoginRateLimitExceededError: If login is rate limited.
        """

        email_block_ttl = await self.redis_service.get_ttl(
            self._login_email_block_key(email)
        )

        ip_block_ttl = await self.redis_service.get_ttl(
            self._login_ip_block_key(client_ip)
        )

        retry_after_seconds = max(email_block_ttl, ip_block_ttl)

        if retry_after_seconds > 0:
            raise TooManyLoginAttemptsError(retry_after_seconds=retry_after_seconds)

    async def _record_failed_login(self, *, email: str, client_ip: str) -> None:
        """
        Record a failed login attempt.

        Args:
            email: User email.
            client_ip: Client IP address.
        """

        email_fail_key = self._login_email_fail_key(email)
        ip_fail_key = self._login_ip_fail_key(client_ip)

        email_fail_count = await self.redis_service.increment_with_ttl(
            email_fail_key, self.settings.login_failed_window_seconds
        )

        ip_fail_count = await self.redis_service.increment_with_ttl(
            ip_fail_key, self.settings.login_failed_window_seconds
        )

        if email_fail_count >= self.settings.login_max_failed_attempts:
            await self.redis_service.set_with_ttl(
                self._login_email_block_key(email),
                "1",
                self.settings.login_block_seconds,
            )

        if ip_fail_count >= self.settings.login_max_failed_attempts:
            await self.redis_service.set_with_ttl(
                self._login_ip_block_key(client_ip),
                "1",
                self.settings.login_block_seconds,
            )

    async def _clear_failed_login(self, *, email: str, client_ip: str) -> None:
        await self.redis_service.delete(
            self._login_email_fail_key(email),
            self._login_email_block_key(email),
            self._login_ip_fail_key(client_ip),
            self._login_ip_block_key(client_ip),
        )

    def _refresh_token_blacklisted_key(self, jti: str) -> str:
        return f"auth:refresh-token:blacklist:{jti}"

    async def blacklist_refresh_token(
        self,
        *,
        jti: str,
        expires_in_seconds: int,
    ) -> None:
        """
        Add refresh token JTI to blacklist.
        """
        logger.info(f"Blacklisting refresh token with JTI: {jti}")
        await self.redis_service.set_with_ttl(
            self._refresh_token_blacklisted_key(jti),
            "1",
            expires_in_seconds,
        )
        logger.info(f"Refresh token with JTI: {jti} blacklisted")

    def _email_action_fail_key(self, *, action: str, email: str) -> str:
        email_key = hash_token(email.lower().strip())
        return f"auth:email-action:{action}:email:{email_key}"

    def _email_action_ip_key(self, *, action: str, client_ip: str) -> str:
        return f"auth:email-action:{action}:ip:{client_ip}"

    def _email_action_block_email_key(self, *, action: str, email: str) -> str:
        email_key = hash_token(email.lower().strip())
        return f"auth:email-action:{action}:block:email:{email_key}"

    def _email_action_block_ip_key(self, *, action: str, client_ip: str) -> str:
        return f"auth:email-action:{action}:block:ip:{client_ip}"

    async def _ensure_email_action_is_not_blocked(
        self,
        *,
        action: str,
        email: str,
        client_ip: str,
    ) -> None:
        email_block_ttl = await self.redis_service.get_ttl(
            self._email_action_block_email_key(action=action, email=email)
        )
        ip_block_ttl = await self.redis_service.get_ttl(
            self._email_action_block_ip_key(action=action, client_ip=client_ip)
        )

        retry_after_seconds = max(email_block_ttl, ip_block_ttl)

        if retry_after_seconds > 0:
            raise TooManyEmailRequestsError(retry_after_seconds=retry_after_seconds)

    async def _record_email_action(
        self,
        *,
        action: str,
        email: str,
        client_ip: str,
    ) -> None:
        email_count = await self.redis_service.increment_with_ttl(
            self._email_action_fail_key(action=action, email=email),
            self.settings.email_action_window_seconds,
        )
        ip_count = await self.redis_service.increment_with_ttl(
            self._email_action_ip_key(action=action, client_ip=client_ip),
            self.settings.email_action_window_seconds,
        )

        if email_count >= self.settings.email_action_max_attempts:
            await self.redis_service.set_with_ttl(
                self._email_action_block_email_key(action=action, email=email),
                "1",
                self.settings.email_action_block_seconds,
            )

        if ip_count >= self.settings.email_action_max_attempts:
            await self.redis_service.set_with_ttl(
                self._email_action_block_ip_key(action=action, client_ip=client_ip),
                "1",
                self.settings.email_action_block_seconds,
            )

    def _refresh_token_blacklisted_key(self, jti: str) -> str:
        return f"auth:refresh-token:blacklist:{jti}"


    async def _ensure_refresh_token_is_not_blacklisted(self, jti: str) -> None:
        ttl = await self.redis_service.get_ttl(self._refresh_token_blacklisted_key(jti))

        if ttl > 0:
            raise TokenInvalidError(token_type="refresh")


    async def _blacklist_refresh_token(self, *, jti: str, exp: int) -> None:
        now = datetime.now(UTC)
        expires_at = datetime.fromtimestamp(exp, tz=UTC)
        ttl_seconds = max(int((expires_at - now).total_seconds()), 0)

        if ttl_seconds <= 0:
            return

        await self.redis_service.set_with_ttl(
            self._refresh_token_blacklisted_key(jti),
            "1",
            ttl_seconds,
        )

    async def logout_all_devices(self, user_id: int) -> None:
        logger.info("Logging out all devices for user_id=%s", user_id)

        token_version = (
            await self.auth_repository.increment_user_token_version(user_id)
        )

        if token_version is None:
            raise TokenInvalidError(token_type="access")
