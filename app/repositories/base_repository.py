from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, db: AsyncSession, model: type[ModelType]) -> None:
        self.db = db
        self.model = model

    async def get_by_id(self, entity_id: int) -> ModelType | None:
        stmt = select(self.model).where(self.model.id == entity_id)  # type: ignore[attr-defined]
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[ModelType]:
        stmt = select(self.model).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        # pyrefly: ignore [missing-attribute]
        obj_data = obj_in.model_dump()
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, entity: ModelType, obj_in: UpdateSchemaType) -> ModelType:
        # pyrefly: ignore [missing-attribute]
        obj_data = obj_in.model_dump(exclude_unset=True)
        for field, value in obj_data.items():
            setattr(entity, field, value)
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def delete(self, id: int) -> None:
        entity = await self.get_by_id(id)
        if not entity:
            raise ValueError(f"Object with id: {id} not found")
        await self.db.delete(entity)
        await self.db.commit()
