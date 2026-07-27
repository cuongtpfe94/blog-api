from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class DatabaseHealthRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def check_connection(self) -> bool:
        result = await self.db.execute(text("SELECT 1"))
        return result.scalar_one() == 1
