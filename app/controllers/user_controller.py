from typing import Annotated

from app.core.responses import list_response, success_response
from app.dependencies.auth import CurrentAdminDep, CurrentUserDep
from app.dependencies.db import get_db
from app.dependencies.user import get_user_service
from app.schemas.request.user_create_request_schema import UserCreateRequest
from app.schemas.response.base import ListData, SuccessResponse
from app.schemas.response.user_out_schema import UserResponse
from app.services.user_service import UserService
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/users", tags=["Users"])

DbSession = Annotated[AsyncSession, Depends(get_db)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]


@router.post(
    "",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create user",
)
async def create_user(
    current_admin: CurrentAdminDep,
    payload: UserCreateRequest,
    user_service: UserServiceDep,
) -> SuccessResponse[UserResponse]:
    user = await user_service.create_user(payload)

    return success_response(UserResponse.model_validate(user))


@router.get(
    "",
    response_model=SuccessResponse[ListData[UserResponse]],
    status_code=status.HTTP_200_OK,
    summary="List User",
)
async def list_users(
    current_admin: CurrentAdminDep,
    user_service: UserServiceDep,
    offset: Annotated[int, Query(ge=0, description="Offset")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Limit")] = 100,
) -> SuccessResponse[ListData[UserResponse]]:
    users, total = await user_service.list_user(offset=offset, limit=limit)

    return list_response(
        [UserResponse.model_validate(user_res) for user_res in users],
        offset=offset,
        limit=limit,
        total=total,
    )


@router.get(
    "/{user_id}",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get user By Id",
)
async def get_user_by_id(
    current_user: CurrentUserDep, user_service: UserServiceDep, user_id: int
) -> SuccessResponse[UserResponse]:
    user_res = await user_service.get_user_by_id(user_id)

    return success_response(UserResponse.model_validate(user_res))
