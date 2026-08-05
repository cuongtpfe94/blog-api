
from pydantic import model_validator
from pydantic import BaseModel, Field

class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    confirm_password: str = Field(..., min_length=8, max_length=128, description="Confirm new password")

    @model_validator(mode="after")
    def validate_password(self) -> "ResetPasswordRequest":
        if self.new_password != self.confirm_password:
          raise ValueError("Password confirmation does not match")
        return self
