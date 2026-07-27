import logging

from app.models.user_model import User
from app.repositories.user_repository import UserRepository
from app.schemas.request.user_create_request_schema import (
    UserCreateDB,
    UserCreateRequest,
)
from app.security.password import hash_password
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.user_repository = UserRepository(db)

    async def create_user(self, payload: UserCreateRequest) -> User:
        """
        Creates a new user

        Args:
          payload: The user creation request schema

        Returns:
          The user response schema

        Raises:
          HTTPException: If the user already exists
        """
        logger.info("Creating user with email=%s", payload.email)

        existing_user = await self.user_repository.get_by_email(payload.email)

        if existing_user is not None:
            logger.warning("User email already exists: %s", payload.email)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User email already exists",
            )

        hashed_password = hash_password(payload.password)

        user = UserCreateDB(
            email=payload.email,
            hashed_password=hashed_password,
            display_name=payload.display_name,
        )

        return await self.user_repository.create(user)

    async def get_user_by_id(self, user_id: int) -> User | None:
        """
        Get user by id

        Args:
          user_id: The user id

        Returns:
          The user response schema

        Raises:
          HTTPException: If the user does not exist
        """
        logger.info("Getting user with id=%s", user_id)

        user = await self.user_repository.get_by_id(user_id)

        if user is None:
            logger.warning("User not found: %s", user_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return user

    async def list_user(self, *, offset: int = 0, limit: int = 100) -> list[User]:
      """
      List user by pagination

      Args:
        offset: The offset
        limit: The limit

      Returns:
        The user list response schema

      Raises:
        HTTPException: If the user does not exist
      """
      logger.info("List all users")

      users = await self.user_repository.list(offset=offset, limit=limit)

      return users
