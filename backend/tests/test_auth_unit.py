import pytest
from datetime import timedelta
import time
from app.core.errors import UnauthorizedError
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hashing_and_verification():
    """Verify passwords are securely hashed and verified with bcrypt."""
    password = "SuperSecretPassword123!"
    hashed = hash_password(password)

    # Hash should not be equal to plaintext
    assert hashed != password
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    # Correct password verifies
    assert verify_password(password, hashed) is True

    # Incorrect password fails
    assert verify_password("WrongPassword123!", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(password, "") is False


def test_password_hashing_empty_raises_error():
    """Verify empty passwords cannot be hashed."""
    with pytest.raises(ValueError):
        hash_password("")


def test_jwt_creation_and_decoding():
    """Verify JWT access tokens are signed and decoded with valid claims."""
    user_id = 42
    token = create_access_token(subject=user_id, extra_claims={"role": "trader"})
    payload = decode_access_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["role"] == "trader"
    assert "exp" in payload
    assert "iat" in payload


def test_jwt_expired_token_handling():
    """Verify expired tokens raise TOKEN_EXPIRED UnauthorizedError."""
    # Create token that expired 10 seconds ago
    token = create_access_token(subject="user_123", expires_delta=timedelta(seconds=-10))

    with pytest.raises(UnauthorizedError) as exc_info:
        decode_access_token(token)

    assert exc_info.value.code == "TOKEN_EXPIRED"
    assert exc_info.value.status_code == 401


def test_jwt_invalid_token_handling():
    """Verify tampered or malformed tokens raise INVALID_TOKEN UnauthorizedError."""
    invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalidpayload.invalidsig"

    with pytest.raises(UnauthorizedError) as exc_info:
        decode_access_token(invalid_token)

    assert exc_info.value.code == "INVALID_TOKEN"
    assert exc_info.value.status_code == 401
