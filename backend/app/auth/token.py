"""
JWT token utilities for authentication.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from .models import TokenPayload

# 30-day token lifetime
ALGORITHM = "HS256"
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "edu-synergy-jwt-secret-change-in-production")
ACCESS_TOKEN_EXPIRE_DAYS = 30


def create_access_token(user_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "role": role,
        "exp": exp,
        "iat": now,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[TokenPayload]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenPayload(**payload)
    except JWTError:
        return None
