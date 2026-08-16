import logging
from typing import Optional
from fastapi import Cookie, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.services.auth import get_user_by_id

logger = logging.getLogger(__name__)


async def get_token_from_request(
    request: Request,
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None),
) -> str:
    """
    Extracts the JWT access token from either the Authorization header or the access_token cookie.
    """
    # 1. Check Authorization Bearer header
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1].strip()
        if token:
            return token

    # 2. Check httpOnly access_token cookie
    if access_token:
        return access_token

    # 3. No token found
    raise UnauthorizedError(
        message="Authentication required. Please log in.",
        code="AUTHENTICATION_REQUIRED",
    )


async def get_current_user(
    token: str = Depends(get_token_from_request),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validates the JWT access token and loads the active user from the database.
    """
    payload = decode_access_token(token)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedError(
            message="Invalid token payload.",
            code="INVALID_TOKEN",
        )

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise UnauthorizedError(
            message="Invalid user identifier in token.",
            code="INVALID_TOKEN",
        )

    user = await get_user_by_id(db, user_id)
    if not user:
        raise UnauthorizedError(
            message="User associated with this token no longer exists.",
            code="USER_NOT_FOUND",
        )

    return user
