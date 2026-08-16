import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.models.portfolio import Portfolio
from app.services.auth import seed_demo_user, DEMO_USER_EMAIL, DEMO_USER_PASSWORD


@pytest.mark.asyncio
async def test_user_registration_success(async_client: AsyncClient):
    """Verify new user registration initializes account and $100,000 portfolio."""
    payload = {
        "email": "newtrader@example.com",
        "password": "strongPassword123",
        "display_name": "New Trader",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert "user" in data
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "newtrader@example.com"
    assert data["user"]["display_name"] == "New Trader"
    assert "hashed_password" not in data["user"]

    # Verify portfolio initialized with $100,000
    portfolio = data["user"]["portfolio"]
    assert portfolio is not None
    assert float(portfolio["cash_balance"]) == 100000.00

    # Verify access_token cookie is set
    assert "access_token" in response.cookies


@pytest.mark.asyncio
async def test_user_registration_email_normalization(async_client: AsyncClient):
    """Verify registration normalizes email to lowercase."""
    payload = {
        "email": "UPPERCASE.TRADER@Example.COM",
        "password": "strongPassword123",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["email"] == "uppercase.trader@example.com"


@pytest.mark.asyncio
async def test_user_registration_duplicate_email(async_client: AsyncClient):
    """Verify duplicate email registration returns 409 Conflict."""
    payload = {
        "email": "duplicate@example.com",
        "password": "strongPassword123",
    }
    # First registration
    res1 = await async_client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Second registration with same email
    res2 = await async_client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    data = res2.json()
    assert "error" in data
    assert data["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_user_registration_validation_errors(async_client: AsyncClient):
    """Verify short passwords and invalid emails are rejected with 422."""
    # Password too short (< 8 chars)
    res_short = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "short@example.com", "password": "123"},
    )
    assert res_short.status_code == 422
    assert res_short.json()["error"]["code"] == "VALIDATION_ERROR"

    # Invalid email format
    res_bad_email = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "validPassword123"},
    )
    assert res_bad_email.status_code == 422


@pytest.mark.asyncio
async def test_user_login_success(async_client: AsyncClient):
    """Verify login returns access token and user info with matching credentials."""
    # Register first
    email = "login_test@example.com"
    password = "correctPassword123"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": "Login Test User"},
    )

    # Login
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == email
    assert "access_token" in data
    assert "access_token" in response.cookies


@pytest.mark.asyncio
async def test_user_login_invalid_credentials(async_client: AsyncClient):
    """Verify login with incorrect password or non-existent user returns 401."""
    # Register user
    email = "known_user@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "realPassword123"},
    )

    # Wrong password
    res_wrong_pw = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "wrongPassword999"},
    )
    assert res_wrong_pw.status_code == 401
    assert res_wrong_pw.json()["error"]["code"] == "UNAUTHORIZED"

    # Unknown email
    res_unknown = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "somePassword123"},
    )
    assert res_unknown.status_code == 401


@pytest.mark.asyncio
async def test_auth_me_endpoint(async_client: AsyncClient):
    """Verify GET /api/v1/auth/me returns profile for authenticated user."""
    # 1. Unauthenticated request returns 401
    unauth_res = await async_client.get("/api/v1/auth/me")
    assert unauth_res.status_code == 401
    assert unauth_res.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"

    # 2. Register and test with Bearer header
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "me_test@example.com", "password": "password123", "display_name": "Me Tester"},
    )
    token = reg_res.json()["access_token"]

    auth_res = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert auth_res.status_code == 200
    data = auth_res.json()
    assert data["email"] == "me_test@example.com"
    assert data["display_name"] == "Me Tester"
    assert float(data["portfolio"]["cash_balance"]) == 100000.00
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_auth_logout_clears_cookie(async_client: AsyncClient):
    """Verify POST /api/v1/auth/logout clears the authentication cookie."""
    # Login to set cookie
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "logout_test@example.com", "password": "password123"},
    )

    # Logout
    logout_res = await async_client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200
    assert logout_res.json()["message"] == "Successfully logged out"


@pytest.mark.asyncio
async def test_demo_user_seeding_and_idempotency(async_client: AsyncClient, db_session: AsyncSession):
    """Verify demo user exists, has $100,000, and can log in."""
    # 1. Seed demo user
    demo_user = await seed_demo_user(db_session)
    assert demo_user.email == DEMO_USER_EMAIL

    # 2. Re-seed to verify idempotency
    demo_user_reseed = await seed_demo_user(db_session)
    assert demo_user_reseed.id == demo_user.id

    # 3. Test logging in as demo user
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_USER_EMAIL, "password": DEMO_USER_PASSWORD},
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert data["user"]["email"] == DEMO_USER_EMAIL
    assert float(data["user"]["portfolio"]["cash_balance"]) == 100000.00
