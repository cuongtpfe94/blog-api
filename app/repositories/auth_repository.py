from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_verification_token_model import EmailVerificationToken
from app.models.password_reset_token_model import PasswordResetToken
from app.models.user_model import User


class AuthRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_user_credentials_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_credentials_by_email(self, email: str) -> User | None:
        """
        Get user credentials by email
        Returns: tuple of (hashed_password, salt)
        """
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_user_password(self, user_id: int, hashed_password: str) -> None:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                hashed_password=hashed_password,
                token_version=User.token_version + 1,
            )
        )

        await self.db.execute(stmt)
        await self.db.commit()

    async def create_password_reset_token(
        self,
        *,
        user_id: int,
        token_hash: str,
        expires_at: datetime,
    ) -> PasswordResetToken:
        token = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        self.db.add(token)
        await self.db.commit()
        await self.db.refresh(token)
        return token

    async def get_password_reset_token_by_hash(
        self,
        token_hash: str,
    ) -> PasswordResetToken | None:
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_password_reset_token_used(
        self, reset_token: PasswordResetToken
    ) -> PasswordResetToken:
        reset_token.is_used = True
        reset_token.used_at = datetime.now(UTC)

        self.db.add(reset_token)
        await self.db.commit()
        await self.db.refresh(reset_token)

        return reset_token

    async def create_email_verification_token(
        self,
        *,
        user_id: int,
        token_hash: str,
        expires_at: datetime,
    ) -> EmailVerificationToken:
        token = EmailVerificationToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        self.db.add(token)
        await self.db.commit()
        await self.db.refresh(token)
        return token

    async def get_email_verification_token_by_hash(
        self,
        token_hash: str,
    ) -> EmailVerificationToken | None:
        stmt = select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_email_verification_token_used(
        self, email_verification_token: EmailVerificationToken
    ) -> EmailVerificationToken:
        email_verification_token.is_used = True
        email_verification_token.used_at = datetime.now(UTC)

        self.db.add(email_verification_token)
        await self.db.commit()
        await self.db.refresh(email_verification_token)

        return email_verification_token

    async def update_user_verified_status(
        self,
        user_id: int,
    ) -> None:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(is_verified=True, verified_at=datetime.now(UTC))
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def increment_user_token_version(self, user_id: int) -> int | None:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(token_version=User.token_version + 1)
            .returning(User.token_version)
        )

        result = await self.db.execute(stmt)
        token_version = result.scalar_one_or_none()

        await self.db.commit()

        return token_version
