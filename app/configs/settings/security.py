from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr

SameSite = Literal["lax", "strict", "none"]
JwtAlgorithm = Literal["HS256", "RS256"]


class JwtSettings(BaseModel):
    """
    JWT settings
    - HS256: secret key must be at least 32 bytes long
    - ALGORITHM: RS256
    """

    model_config = ConfigDict(frozen=True)
    secret_key: SecretStr = Field(...)
    algorithm: JwtAlgorithm = Field(default="HS256")
    issuer: str = Field(...)
    audience: str = Field(...)

    access_token_expire_minutes: int = Field(default=30)


class SecuritySettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    jwt: JwtSettings
