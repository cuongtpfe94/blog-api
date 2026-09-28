from app.dependencies.redis import get_redis_service
from app.dependencies.email import get_email_service
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.core.exceptions.auth_exceptions import (
    PermissionDeniedError,
    TokenInvalidError,
    TokenMissingError,
)
from app.dependencies.db import get_db
from app.models.user_model import User
from app.security.provider import get_jwt_service
from app.services.auth_service import AuthService
from app.services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def get_auth_service() -> AsyncGenerator[AuthService, None]:
    """
    Dependency to get the auth service
    """
    email_service = get_email_service()
    redis_service = get_redis_service()

    async for db in get_db():
        yield AuthService(db, email_service=email_service, redis_service=redis_service)


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> User:
    if token is None:
        raise TokenMissingError(token_type="access")

    jwt_service = get_jwt_service()
    payload = jwt_service.decode_access_token(token)

    subject = payload.get("sub")
    if subject is None:
        raise TokenInvalidError(token_type="access")

    try:
        user_id = int(subject)
    except ValueError as err:
        raise TokenInvalidError(token_type="access") from err

    async for db in get_db():
        user_service = UserService(db)
        user = await user_service.get_user_by_id(user_id)

        if user is None:
            raise TokenInvalidError(token_type="access")
        return user

    raise TokenInvalidError(token_type="access")


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_superuser:
        raise PermissionDeniedError(reason="admin_required")
    return current_user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
CurrentAdminDep = Annotated[User, Depends(get_current_admin)]
