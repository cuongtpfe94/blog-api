from app.schemas.response.two_factor_out_schema import TwoFactorChallengeResponse
from app.core.exceptions.auth_exceptions import TokenMissingError
from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from app.schemas.request.resend_verification_email_request_schema import (
    ResendVerificationEmailRequest,
)
from typing import Annotated

from app.core.responses import success_response
from app.dependencies.auth import CurrentUserDep, get_auth_service
from app.dependencies.registration import get_registration_service
from app.schemas.request.change_password_request_schema import ChangePasswordRequest
from app.schemas.request.forgot_password_request_schema import ForgotPasswordRequest
from app.schemas.request.login_request_schema import LoginRequest
from app.schemas.request.register_request_schema import RegisterRequest
from app.schemas.request.reset_password_request_schema import ResetPasswordRequest
from app.schemas.request.verify_email_request_schema import VerifyEmailRequest
from app.schemas.response.base import SuccessResponse
from app.schemas.response.token_out_schema import TokenResponse
from app.schemas.response.user_out_schema import UserResponse
from app.services.auth_service import AuthService, TwoFactorChallengeTokenOut, TokenPairOut
from app.services.registration_service import RegistrationService

router = APIRouter(prefix="/auth", tags=["Auth"])

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
RegistrationServiceDep = Annotated[
    RegistrationService,
    Depends(get_registration_service),
]

RefreshTokenCookie = Annotated[str | None, Cookie(alias="refresh_token")]

def set_refresh_token_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=30 * 24 * 60 * 60,
        path="/auth",
    )


@router.post(
    "/login",
    response_model=SuccessResponse[TokenResponse | TwoFactorChallengeResponse],
    status_code=status.HTTP_200_OK,
)
async def login(
    request: Request,
    response: Response,
    payload: LoginRequest,
    auth_service: AuthServiceDep
) -> SuccessResponse[TokenResponse | TwoFactorChallengeResponse]:
    client_ip = request.client.host if request.client else "unknown_ip"

    auth_service_res = await auth_service.login(
        email=payload.email, password=payload.password, client_ip=client_ip
    )

    if isinstance(auth_service_res, TokenPairOut):
        set_refresh_token_cookie(response, auth_service_res.refresh_token)


        return success_response(
            TokenResponse.model_validate(auth_service_res, from_attributes=True)
        )

    if isinstance(auth_service_res, TwoFactorChallengeTokenOut):
        return success_response(
            TwoFactorChallengeResponse.model_validate(auth_service_res, from_attributes=True)
        )

    raise RuntimeError("Unsupported auth service response type")


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
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Change user password",
)
async def change_password(
    response: Response,
    payload: ChangePasswordRequest,
    current_user: CurrentUserDep,
    auth_service: AuthServiceDep,
) -> SuccessResponse[None]:
    await auth_service.change_password(
        email=current_user.email,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )

    response.delete_cookie(
        key="refresh_token",
        path="/auth",
    )

    return success_response(message="Password changed successfully")


@router.post(
    "/forgot-password",
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Forgot password",
)
async def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    auth_service: AuthServiceDep,
) -> SuccessResponse[None]:
    client_ip = request.client.host if request.client else "unknown_ip"

    await auth_service.forgot_password(email=payload.email, client_ip=client_ip)

    return success_response(message="Forgot password successfully")


@router.post(
    "/reset-password",
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Reset password",
)
async def reset_password(
    response: Response,
    payload: ResetPasswordRequest,
    auth_service: AuthServiceDep,
) -> SuccessResponse[None]:
    await auth_service.reset_password(
        token=payload.token,
        new_password=payload.new_password,
    )

    response.delete_cookie(
        key="refresh_token",
        path="/auth",
    )

    return success_response(message="Password reset successfully")


@router.post(
    "/verify-email",
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Verify email",
)
async def verify_email(
    payload: VerifyEmailRequest,
    auth_service: AuthServiceDep,
) -> SuccessResponse[None]:
    await auth_service.verify_email(
        token=payload.token,
    )

    return success_response(message="Email verified successfully")


@router.post(
    "/register",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    payload: RegisterRequest,
    registration_service: RegistrationServiceDep,
) -> SuccessResponse[UserResponse]:
    user = await registration_service.register(payload)

    return success_response(user)


@router.post(
    "/resend-verification-email",
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Resend verification email",
)
async def resend_verification_email(
    request: Request,
    payload: ResendVerificationEmailRequest,
    auth_service: AuthServiceDep,
) -> SuccessResponse[None]:
    client_ip = request.client.host if request.client else "unknown_ip"

    await auth_service.resend_verification_email(
        email=payload.email, client_ip=client_ip
    )

    return success_response(message="Verification email resent successfully")


@router.post(
    "/refresh",
    response_model=SuccessResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
)
async def refresh(
    refresh_token: RefreshTokenCookie,
    auth_service: AuthServiceDep,
) -> SuccessResponse[TokenResponse]:
    if refresh_token is None:
        raise TokenMissingError(token_type="refresh")

    auth_service_res = await auth_service.refresh(refresh_token)

    return success_response(
        TokenResponse.model_validate(auth_service_res, from_attributes=True)
    )


@router.post(
    "/logout",
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Logout current device",
)
async def logout(
    response: Response,
    refresh_token: RefreshTokenCookie,
    auth_service: AuthServiceDep,
) -> SuccessResponse[None]:
    if refresh_token is None:
        raise TokenMissingError(token_type="refresh")

    await auth_service.logout(refresh_token)

    response.delete_cookie(
        key="refresh_token",
        path="/auth",
    )

    return success_response(message="Logged out successfully")

@router.post(
    "/logout-all-devices",
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Logout all devices",
)
async def logout_all_devices(
    response: Response,
    current_user: CurrentUserDep,
    auth_service: AuthServiceDep,
) -> SuccessResponse[None]:
    await auth_service.logout_all_devices(current_user.id)

    response.delete_cookie(
        key="refresh_token",
        path="/auth",
    )

    return success_response(
        message="Logged out from all devices successfully"
    )
