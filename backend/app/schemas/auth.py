from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")
    display_name: Optional[str] = Field(None, max_length=100, description="Optional public display name")

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., min_length=1, description="Password")

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class PortfolioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    cash_balance: float
    created_at: datetime
    updated_at: datetime


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: Optional[str] = None
    created_at: datetime
    portfolio: Optional[PortfolioResponse] = None


class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"
