from uuid import uuid4
from datetime import UTC, datetime, timedelta
from typing import Any

from app.configs.settings.security import JwtSettings
from app.core.exceptions.auth_exceptions import TokenExpiredError, TokenInvalidError
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError


class JWTService:
    def __init__(self, settings: JwtSettings) -> None:
        self.__settings = settings

    def create_access_token(
        self, *, subject: str, extra_claims: dict[str, Any] | None = None
    ) -> str:
        now = datetime.now(UTC)
        jti = str(uuid4())

        payload: dict[str, Any] = {
            "sub": subject,
            "jti": jti,
            "iss": self.__settings.issuer,
            "aud": self.__settings.audience,
            "iat": now,
            "exp": (
                now + timedelta(minutes=self.__settings.access_token_expire_minutes)
            ),
            "type": "access",
        }

        if extra_claims:
            payload.update(extra_claims)

        return jwt.encode(
            payload,
            self.__settings.secret_key.get_secret_value(),
            algorithm=self.__settings.algorithm,
        )

    def decode_access_token(self, token: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                self.__settings.secret_key.get_secret_value(),
                algorithms=[self.__settings.algorithm],
                issuer=self.__settings.issuer,
                audience=self.__settings.audience,
            )
        except ExpiredSignatureError as err:
            raise TokenExpiredError(token_type="access") from err
        except JWTError as err:
            raise TokenInvalidError(token_type="access") from err

        if payload.get("type") != "access":
            raise TokenInvalidError(token_type="access")

        return payload

    def create_refresh_token(
        self, *, subject: str, extra_claims: dict[str, Any] | None = None
    ) -> str:
        now = datetime.now(UTC)
        jti = str(uuid4())

        payload: dict[str, Any] = {
            "sub": subject,
            "jti": jti,
            "iss": self.__settings.issuer,
            "aud": self.__settings.audience,
            "iat": now,
            "exp": (
                now + timedelta(days=self.__settings.refresh_token_expire_days)
            ),
            "type": "refresh",
        }

        if extra_claims:
            payload.update(extra_claims)

        return jwt.encode(
            payload,
            self.__settings.secret_key.get_secret_value(),
            algorithm=self.__settings.algorithm,
        )

    def decode_refresh_token(self, token: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                self.__settings.secret_key.get_secret_value(),
                algorithms=[self.__settings.algorithm],
                issuer=self.__settings.issuer,
                audience=self.__settings.audience,
            )
        except ExpiredSignatureError as err:
            raise TokenExpiredError(token_type="refresh") from err
        except JWTError as err:
            raise TokenInvalidError(token_type="refresh") from err

        if payload.get("type") != "refresh":
            raise TokenInvalidError(token_type="refresh")

        if not payload.get("sub") or not payload.get("jti"):
            raise TokenInvalidError(token_type="refresh")

        return payload
