from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(min_length=8, max_length=128, description="Password")
    display_name: str = Field(min_length=3, max_length=100, description="Display name")
