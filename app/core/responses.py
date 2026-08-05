from typing import TypeVar

from app.schemas.response.base import ListData, Meta, SuccessResponse

T = TypeVar("T")


def success_response(
    data: T | None = None,
    *,
    message: str | None = None,
) -> SuccessResponse[T]:
    return SuccessResponse(data=data, message=message)


def list_response(
    data: list[T],
    *,
    offset: int,
    limit: int,
    total: int,
    message: str | None = None,
) -> SuccessResponse[ListData[T]]:
    return SuccessResponse(
        data=ListData(items=data, meta=Meta(offset=offset, limit=limit, total=total)),
        message=message,
    )
