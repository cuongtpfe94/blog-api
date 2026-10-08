from typing import Literal

from pydantic import BaseModel

class TwoFactorChallengeResponse(BaseModel):
    requires_2fa: Literal[True] = True
    challenge_token: str
    expires_in: int
