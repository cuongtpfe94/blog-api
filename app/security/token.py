import secrets
from hashlib import sha256


def generate_secure_token() -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash a token"""
    return sha256(token.encode("utf-8")).hexdigest()
