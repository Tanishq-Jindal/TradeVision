import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, Union
import bcrypt
import jwt
from app.core.config import settings
from app.core.errors import UnauthorizedError

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using bcrypt with a generated salt.
    """
    if not password:
        raise ValueError("Password cannot be empty")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext password against a stored bcrypt hash.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception as e:
        logger.warning(f"Password verification error: {str(e)}")
        return False


def create_access_token(
    subject: Union[str, int],
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generates a signed JWT access token.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.JWT_EXPIRY_MINUTES)

    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        to_encode.update(extra_claims)

    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a JWT access token.
    Raises UnauthorizedError on invalid/expired signatures.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[ALGORITHM],
            options={"verify_exp": True},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Token has expired", code="TOKEN_EXPIRED")
    except jwt.InvalidTokenError as e:
        raise UnauthorizedError(f"Invalid token: {str(e)}", code="INVALID_TOKEN")
