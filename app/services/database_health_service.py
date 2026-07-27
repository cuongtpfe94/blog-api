import logging

from app.repositories.database_health_repository import DatabaseHealthRepository
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DatabaseHealthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.health_repository = DatabaseHealthRepository(db)

    async def check_database_connection(self) -> bool:
        """
        Check whether the application can connect to the database.

        Returns:
            True if the database connection is healthy.
        """
        try:
            return await self.health_repository.check_connection()
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return False
