from pydantic import BaseModel, EmailStr, Field


class ResendVerificationEmailRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address")
