from sqlalchemy.util.typing import Literal
from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    expires_in: int
    token_type: str = "Bearer"
    requires_2fa: Literal[False] = False

