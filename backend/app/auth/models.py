"""
Pydantic models for user authentication and token management.
"""
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field


class User(BaseModel):
    """Internal user representation stored in SQLite."""
    id: str
    username: str
    hashed_password: str
    role: str  # admin | teacher | web_teacher | student
    subject: str = "通用学科"
    is_active: bool = True


class UserCreate(BaseModel):
    username: str
    password: str = ""
    role: str
    subject: str = "通用学科"
    id: str = ""  # optional: if empty, falls back to username


class UserInDB(User):
    """User with hashed password (stored in DB)."""
    pass


class TokenPayload(BaseModel):
    sub: str  # user_id
    role: str
    exp: datetime
    iat: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    subject: str