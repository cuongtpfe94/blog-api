from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    display_name: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    is_verified: bool
    verified_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
