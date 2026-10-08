from pydantic import BaseModel, Field


class TwoFactorVerifyRequest(BaseModel):
    challenge_token: str = Field(
        ...,
        min_length=32,
        max_length=256,
    )
    otp: str = Field(
        ...,
        pattern=r"^\d{6}$",
        description="Six-digit verification code",
    )
