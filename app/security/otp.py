import hashlib
import hmac
import secrets


def generate_otp(length: int = 6) -> str:
    if length <= 0:
        raise ValueError("OTP length must be greater than zero")

    upper_bound = 10**length
    value = secrets.randbelow(upper_bound)

    return f"{value:0{length}d}"


def hash_otp(otp: str, pepper: str) -> str:
    return hmac.new(
        pepper.encode("utf-8"),
        otp.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_otp(
    plain_otp: str,
    expected_hash: str,
    pepper: str,
) -> bool:
    actual_hash = hash_otp(plain_otp, pepper)

    return hmac.compare_digest(actual_hash, expected_hash)
