from app.schemas.request.reset_password_request_schema import ResetPasswordRequest
from typing import Annotated

from app.core.responses import success_response
from app.dependencies.auth import CurrentUserDep, get_auth_service
from app.schemas.request.change_password_request_schema import ChangePasswordRequest
from app.schemas.request.forgot_password_request_schema import ForgotPasswordRequest
from app.schemas.request.login_request_schema import LoginRequest
from app.schemas.response.base import SuccessResponse
from app.schemas.response.token_out_schema import TokenResponse
from app.schemas.response.user_out_schema import UserResponse
from app.services.auth_service import AuthService
from fastapi import APIRouter, Depends, status

router = APIRouter(prefix="/auth", tags=["Auth"])

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


@router.post(
    "/login",
    response_model=SuccessResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
)
async def login(
    payload: LoginRequest, auth_service: AuthServiceDep
) -> SuccessResponse[TokenResponse]:
    auth_service_res = await auth_service.login(
        email=payload.email, password=payload.password
    )

    return success_response(
        TokenResponse.model_validate(auth_service_res, from_attributes=True)
    )


@router.get(
    "/me",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get current user",
)
async def get_me(current_user: CurrentUserDep) -> SuccessResponse[UserResponse]:
    return success_response(UserResponse.model_validate(current_user))


@router.patch(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change user password",
)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: CurrentUserDep,
    auth_service: AuthServiceDep,
) -> SuccessResponse[None]:
    await auth_service.change_password(
        email=current_user.email,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )

    return success_response(message="Password changed successfully")


@router.post(
    "/forgot-password",
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Forgot password",
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    auth_service: AuthServiceDep,
) -> SuccessResponse[None]:
    await auth_service.forgot_password(email=payload.email)

    return success_response(message="Forgot password successfully")

@router.post(
    "/reset-password",
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Reset password",
)
async def reset_password(
    payload: ResetPasswordRequest,
    auth_service: AuthServiceDep,
) -> SuccessResponse[None]:
    await auth_service.reset_password(
        token=payload.token,
        new_password=payload.new_password,
    )

    return success_response(message="Password reset successfully")
