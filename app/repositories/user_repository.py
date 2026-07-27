from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_model import User
from app.repositories.base_repository import BaseRepository
from app.schemas.request.user_create_request_schema import UserCreateDB


class UserRepository(BaseRepository[User, UserCreateDB, dict]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, model=User)

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
