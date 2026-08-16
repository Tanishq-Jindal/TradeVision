import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ConflictError, UnauthorizedError
from app.core.security import hash_password, verify_password
from app.models.portfolio import Portfolio
from app.models.user import User
from app.schemas.auth import UserLoginRequest, UserRegisterRequest

logger = logging.getLogger(__name__)

DEMO_USER_EMAIL = "demo@tradewise.cloud"
DEMO_USER_PASSWORD = "demo123"
INITIAL_PORTFOLIO_CASH = 100000.00


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Retrieves a user by normalized email with eager-loaded portfolio.
    """
    stmt = (
        select(User)
        .options(selectinload(User.portfolio))
        .where(User.email == email.strip().lower())
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """
    Retrieves a user by ID with eager-loaded portfolio.
    """
    stmt = (
        select(User)
        .options(selectinload(User.portfolio))
        .where(User.id == user_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def register_user(db: AsyncSession, register_data: UserRegisterRequest) -> User:
    """
    Registers a new user and automatically initializes their $100,000 portfolio.
    Raises ConflictError if the email is already registered.
    """
    normalized_email = register_data.email.strip().lower()
    existing_user = await get_user_by_email(db, normalized_email)
    if existing_user:
        raise ConflictError(
            message="An account with this email address already exists.",
            details={"code": "EMAIL_ALREADY_EXISTS"},
        )

    # Hash password securely
    hashed_pwd = hash_password(register_data.password)

    # Create User
    new_user = User(
        email=normalized_email,
        hashed_password=hashed_pwd,
        display_name=register_data.display_name.strip() if register_data.display_name else None,
    )
    db.add(new_user)
    await db.flush()  # Populates new_user.id

    # Create Portfolio with initial $100,000
    portfolio = Portfolio(
        user_id=new_user.id,
        cash_balance=INITIAL_PORTFOLIO_CASH,
    )
    db.add(portfolio)
    await db.commit()

    # Re-fetch user with portfolio loaded
    user = await get_user_by_id(db, new_user.id)
    if not user:
        raise RuntimeError("Failed to retrieve created user")
    
    logger.info(f"Registered new user id={user.id} email={user.email}")
    return user


async def authenticate_user(db: AsyncSession, login_data: UserLoginRequest) -> User:
    """
    Authenticates a user with email and password.
    Returns the user if credentials match; raises UnauthorizedError otherwise.
    """
    normalized_email = login_data.email.strip().lower()
    user = await get_user_by_email(db, normalized_email)

    if not user or not verify_password(login_data.password, user.hashed_password):
        # Generic error message to prevent account enumeration
        logger.info(f"Failed login attempt for email={normalized_email}")
        raise UnauthorizedError(
            message="Invalid email or password.",
            details={"code": "INVALID_CREDENTIALS"},
        )

    logger.info(f"User authenticated successfully id={user.id} email={user.email}")
    return user


async def seed_demo_user(db: AsyncSession) -> User:
    """
    Idempotently seeds the demo user (demo@tradewise.cloud / demo123) with a $100,000 portfolio.
    If the demo user already exists, returns the existing record without resetting portfolio balance.
    """
    existing_user = await get_user_by_email(db, DEMO_USER_EMAIL)
    if existing_user:
        logger.info(f"Demo user already exists (id={existing_user.id}); preserving state.")
        return existing_user

    hashed_pwd = hash_password(DEMO_USER_PASSWORD)
    demo_user = User(
        email=DEMO_USER_EMAIL,
        hashed_password=hashed_pwd,
        display_name="Demo Trader",
    )
    db.add(demo_user)
    await db.flush()

    portfolio = Portfolio(
        user_id=demo_user.id,
        cash_balance=INITIAL_PORTFOLIO_CASH,
    )
    db.add(portfolio)
    await db.commit()

    user = await get_user_by_id(db, demo_user.id)
    if not user:
        raise RuntimeError("Failed to seed demo user")

    logger.info(f"Successfully seeded demo user id={user.id} email={DEMO_USER_EMAIL} with ${INITIAL_PORTFOLIO_CASH} cash.")
    return user
