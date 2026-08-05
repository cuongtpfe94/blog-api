from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Meta(BaseModel):
    offset: int
    limit: int
    total: int


class ListData(BaseModel, Generic[T]):
    items: list[T]
    meta: Meta


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    message: str | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error_code: str
    message: str | None = None
    extra: dict | None = None
