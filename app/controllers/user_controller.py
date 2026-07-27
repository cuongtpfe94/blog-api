from app.schemas.response.base import ListData
from app.core.responses import list_response
from app.dependencies import user
from app.schemas.response.base import SuccessResponse
from fastapi import Query
from app.dependencies.user import get_user_service
from app.dependencies.db import get_db
from app.schemas.request.user_create_request_schema import UserCreateRequest
from app.schemas.response.user_out_schema import UserResponse
from app.services.user_service import UserService
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.util.typing import Annotated
from app.core.responses import success_response

router = APIRouter(prefix="/users", tags=["Users"])

DbSession = Annotated[AsyncSession, Depends(get_db)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]


@router.post(
    "",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create user",
)
async def create_user(payload: UserCreateRequest, user_service: UserServiceDep) -> SuccessResponse[UserResponse]:
    user = await user_service.create_user(payload)

    return success_response(UserResponse.model_validate(user))

@router.get(
    "",
    response_model=SuccessResponse[ListData[UserResponse]],
    status_code=status.HTTP_200_OK,
    summary="List User"
)
async def list_users(
    user_service: UserServiceDep,
    offset: Annotated[int, Query(ge=0, description="Offset")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Limit")] = 100,
) -> SuccessResponse[ListData[UserResponse]]:
    users = await user_service.list_user(offset=offset, limit=limit)

    return list_response([UserResponse.model_validate(user) for user in users], offset=offset, limit=limit, total=0)

@router.get(
    "/{user_id}",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get user By Id",
)
async def get_user_by_id(
    user_service: UserServiceDep,
    user_id: int
) -> SuccessResponse[UserResponse]:
    user = await user_service.get_user_by_id(user_id)

    return success_response(UserResponse.model_validate(user))
