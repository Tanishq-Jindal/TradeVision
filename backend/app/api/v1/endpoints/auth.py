import logging
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth import authenticate_user, register_user

logger = logging.getLogger(__name__)

router = APIRouter()


def set_auth_cookie(response: Response, token: str) -> None:
    """
    Sets the access_token in an httpOnly cookie.
    """
    cookie_max_age = settings.JWT_EXPIRY_MINUTES * 60
    is_production = settings.ENV.lower() == "production"
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=cookie_max_age,
        expires=cookie_max_age,
        httponly=True,
        secure=is_production,
        samesite="lax",
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    """
    Clears the access_token cookie.
    """
    is_production = settings.ENV.lower() == "production"
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        secure=is_production,
        samesite="lax",
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description="Registers a new user, automatically initializes their $100,000 virtual portfolio, sets an httpOnly session cookie, and returns a JWT bearer token.",
)
async def register(
    register_data: UserRegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    user = await register_user(db, register_data)
    token = create_access_token(subject=user.id)
    set_auth_cookie(response, token)
    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=token,
        token_type="bearer",
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Log in with email and password",
    description="Authenticates credentials, sets an httpOnly session cookie, and returns a JWT bearer token.",
)
async def login(
    login_data: UserLoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    user = await authenticate_user(db, login_data)
    token = create_access_token(subject=user.id)
    set_auth_cookie(response, token)
    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=token,
        token_type="bearer",
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
    description="Returns the profile and portfolio summary for the currently authenticated user.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Log out current session",
    description="Clears the authentication session cookie.",
)
async def logout(response: Response) -> dict:
    clear_auth_cookie(response)
    return {"message": "Successfully logged out"}
