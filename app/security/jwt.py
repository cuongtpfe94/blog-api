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

        payload: dict[str, Any] = {
            "sub": subject,
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
