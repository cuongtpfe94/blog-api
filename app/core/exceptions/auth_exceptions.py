from http import HTTPStatus
from typing import Literal

from app.core.exceptions.base import BaseAPIError

TokenType = Literal["access", "refresh", "unknown"]


def _error_code(base: str, token_type: TokenType = "unknown") -> str:
    """
    base: 'TOKEN_MISSING', 'TOKEN_EXPIRED', 'TOKEN_INVALID', 'INVALID_CREDENTIALS'
    token_type: 'access', 'refresh', 'unknow'
    """
    if token_type == "access":
        prefix = "AUTH_ACCESS"
    elif token_type == "refresh":
        prefix = "AUTH_REFRESH"
    else:
        prefix = "AUTH"

    return f"{prefix}_{base}"


class InvalidCredentialsError(BaseAPIError):
    def __init__(
        self, token_type: TokenType = "unknown", *, reason: str | None = None
    ) -> None:
        extra: dict[str, str | TokenType] = {"token_type": token_type}

        if reason:
            extra["reason"] = reason

        super().__init__(
            message="Invalid email or password",
            error_code=_error_code("INVALID_CREDENTIALS", token_type),
            status_code=HTTPStatus.UNAUTHORIZED,
            extra=extra,
        )


class TokenExpiredError(BaseAPIError):
    def __init__(self, token_type: TokenType = "access") -> None:
        super().__init__(
            message="Authentication token has expired",
            error_code=_error_code("TOKEN_EXPIRED", token_type),
            status_code=HTTPStatus.UNAUTHORIZED,
            extra={"token_type": token_type},
        )


class TokenInvalidError(BaseAPIError):
    def __init__(self, token_type: TokenType = "access") -> None:
        super().__init__(
            message="Authentication token is invalid",
            error_code=_error_code("TOKEN_INVALID", token_type),
            status_code=HTTPStatus.UNAUTHORIZED,
            extra={"token_type": token_type},
        )


class TokenMissingError(BaseAPIError):
    def __init__(self, token_type: TokenType = "access") -> None:
        super().__init__(
            message="Authentication token is missing",
            error_code=_error_code("TOKEN_MISSING", token_type),
            status_code=HTTPStatus.UNAUTHORIZED,
            extra={"token_type": token_type},
        )


class UserInactiveError(BaseAPIError):
    def __init__(
        self, token_type: TokenType = "unknown", *, reason: str | None = None
    ) -> None:
        extra: dict[str, str | TokenType] = {"token_type": token_type}

        if reason:
            extra["reason"] = reason

        super().__init__(
            message="User is inactive",
            error_code=_error_code("USER_INACTIVE"),
            status_code=HTTPStatus.UNAUTHORIZED,
            extra=extra,
        )


class PermissionDeniedError(BaseAPIError):
    def __init__(self, *, reason: str | None = None) -> None:
        extra: dict[str, str] = {}

        if reason:
            extra["reason"] = reason

        super().__init__(
            message="Permission denied",
            error_code=_error_code("PERMISSION_DENIED"),
            status_code=HTTPStatus.FORBIDDEN,
            extra=extra,
        )


class PasswordResetTokenInvalidError(BaseAPIError):
    def __init__(self) -> None:
        super().__init__(
            message="Invalid password reset token",
            error_code=_error_code("PASSWORD_RESET_TOKEN_INVALID"),
            status_code=HTTPStatus.BAD_REQUEST,
            extra={},
        )


class PasswordResetTokenExpiredError(BaseAPIError):
    def __init__(self) -> None:
        super().__init__(
            message="Password reset token has expired",
            error_code=_error_code("PASSWORD_RESET_TOKEN_EXPIRED"),
            status_code=HTTPStatus.BAD_REQUEST,
            extra={},
        )


class PasswordResetTokenUsedError(BaseAPIError):
    def __init__(self) -> None:
        super().__init__(
            message="Password reset token has been used",
            error_code=_error_code("PASSWORD_RESET_TOKEN_USED"),
            status_code=HTTPStatus.BAD_REQUEST,
            extra={},
        )


class EmailVerificationTokenInvalidError(BaseAPIError):
    def __init__(self) -> None:
        super().__init__(
            message="Email verification link is invalid",
            error_code=_error_code("EMAIL_VERIFICATION_TOKEN_INVALID"),
            status_code=HTTPStatus.BAD_REQUEST,
            extra={},
        )


class EmailVerificationTokenExpiredError(BaseAPIError):
    def __init__(self) -> None:
        super().__init__(
            message="Email verification link has expired",
            error_code=_error_code("EMAIL_VERIFICATION_TOKEN_EXPIRED"),
            status_code=HTTPStatus.BAD_REQUEST,
            extra={},
        )


class EmailVerificationTokenUsedError(BaseAPIError):
    def __init__(self) -> None:
        super().__init__(
            message="Email verification link has been used",
            error_code=_error_code("EMAIL_VERIFICATION_TOKEN_USED"),
            status_code=HTTPStatus.BAD_REQUEST,
            extra={},
        )


class EmailVerificationAlreadyVerifiedError(BaseAPIError):
    def __init__(self) -> None:
        super().__init__(
            message="Email has already been verified",
            error_code=_error_code("EMAIL_VERIFICATION_ALREADY_VERIFIED"),
            status_code=HTTPStatus.BAD_REQUEST,
            extra={},
        )


class EmailNotVerifiedError(BaseAPIError):
    def __init__(self) -> None:
        super().__init__(
            message="Email is not verified",
            error_code=_error_code("EMAIL_NOT_VERIFIED"),
            status_code=HTTPStatus.BAD_REQUEST,
            extra={},
        )


class TooManyEmailRequestsError(BaseAPIError):
    def __init__(self, *, retry_after_seconds: int) -> None:
        super().__init__(
            message="Too many email action requests. Please try again later.",
            error_code=_error_code("TOO_MANY_EMAIL_ACTION_REQUESTS"),
            status_code=HTTPStatus.TOO_MANY_REQUESTS,
            extra={"retry_after_seconds": str(retry_after_seconds)},
        )


class TooManyLoginAttemptsError(BaseAPIError):
    def __init__(self, *, retry_after_seconds: int) -> None:
        super().__init__(
            message="Too many login attempts. Please try again later.",
            error_code=_error_code("TOO_MANY_LOGIN_ATTEMPTS"),
            status_code=HTTPStatus.TOO_MANY_REQUESTS,
            extra={"retry_after_seconds": str(retry_after_seconds)},
        )

class TwoFactorChallengeInvalidError(BaseAPIError):
    def __init__(self)-> None:
        super().__init__(
            message="Two-factor challenge is invalid or has expired.",
            error_code=_error_code("TWO_FACTOR_CHALLENGE_INVALID"),
            status_code=HTTPStatus.UNAUTHORIZED,
            extra={},
        )


class TwoFactorCodeInvalidError(BaseAPIError):
    def __init__(self) -> None:
        super().__init__(
            message="Two-factor verification code is invalid",
            error_code=_error_code("TWO_FACTOR_CODE_INVALID"),
            status_code=HTTPStatus.UNAUTHORIZED,
            extra={},
        )
