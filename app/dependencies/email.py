from app.services.email_service import EmailService
from functools import lru_cache


@lru_cache(maxsize=1)
def get_email_service() -> EmailService:
    return EmailService()
