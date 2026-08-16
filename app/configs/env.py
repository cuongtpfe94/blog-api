from functools import lru_cache
from typing import Any

from app.configs.settings.security import JwtAlgorithm, JwtSettings, SecuritySettings
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Any, Literal

EmailProvider = Literal["console", "ses"]


class Settings(BaseSettings):
    app_name: str = Field(default="Blog API", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    app_description: str = Field(
        default="Personal blog API built with FastAPI and PostgreSQL",
        alias="APP_DESCRIPTION",
    )
    debug: bool = Field(default=True, alias="DEBUG")
    database_url: str = Field(alias="DATABASE_URL")

    jwt_secret_key: SecretStr = Field(alias="JWT_SECRET_KEY")
    jwt_issuer: str = Field(..., validation_alias="JWT_ISSUER")
    jwt_audience: str = Field(..., validation_alias="JWT_AUDIENCE")
    jwt_algorithm: JwtAlgorithm = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    security: SecuritySettings | None = Field(default=None)

    frontend_url: str = Field(alias="FRONTEND_URL")
    email_from: str = Field(default="no-reply@example.com", alias="EMAIL_FROM")
    email_provider: EmailProvider = Field(default="console", alias="EMAIL_PROVIDER")
    aws_region: str = Field(..., alias="AWS_REGION")
    aws_access_key_id: str = Field(..., alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(..., alias="AWS_SECRET_ACCESS_KEY")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def model_post_init(self, __context: Any) -> None:
        jwt_settings = self._build_jwt_settings()
        self.security = SecuritySettings(jwt=jwt_settings)

    def _build_jwt_settings(self) -> JwtSettings:
        issuer = (self.jwt_issuer or "").strip()
        audience = (self.jwt_audience or "").strip()
        secret_key = self.jwt_secret_key.get_secret_value().strip()

        return JwtSettings(
            issuer=issuer,
            audience=audience,
            secret_key=secret_key,
            algorithm=self.jwt_algorithm,
            access_token_expire_minutes=self.jwt_access_token_expire_minutes,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
