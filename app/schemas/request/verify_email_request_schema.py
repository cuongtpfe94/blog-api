from pydantic import BaseModel, Field


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=32, description="Email verification token")
