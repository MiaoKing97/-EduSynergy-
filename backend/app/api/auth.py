"""
Auth API: login, register, get current user, list users.
"""
from fastapi import APIRouter, Depends, HTTPException, status
import logging
from ..auth.store import UserStore, verify_password

logger = logging.getLogger(__name__)
from ..auth.models import LoginRequest, AuthResponse, UserCreate, UserInDB
from ..auth.token import create_access_token, decode_access_token

router = APIRouter()
user_store = UserStore()


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    user = await user_store.get_user_by_username(req.username)
    if not user:
        logger.warning(f"Login failed: user '{req.username}' not found")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if not verify_password(req.password, user.hashed_password):
        logger.warning(f"Login failed: user '{req.username}' password mismatch (input len={len(req.password)}, stored hash={user.hashed_password[:15]})")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已禁用")

    token = create_access_token(user.id, user.role)
    return AuthResponse(
        access_token=token,
        token_type="bearer",
        role=user.role,
        username=user.username,
        subject=user.subject,
    )


@router.post("/register", response_model=AuthResponse)
async def register(req: UserCreate):
    logger.info(f"Register: username={req.username}, id={req.id}, has_password={bool(req.password)}")
    existing = await user_store.get_user_by_username(req.username)
    if existing:
        # Username already exists — update password, role, and subject
        if not req.password:
            # No password provided — only update role and subject
            updated = await user_store.update_user(
                existing.id,
                role=req.role,
                subject=req.subject,
            )
        else:
            updated = await user_store.update_user(
                existing.id,
                password=req.password,
                role=req.role,
                subject=req.subject,
            )
        return AuthResponse(
            access_token=updated.id,
            token_type="bearer",
            role=updated.role,
            username=updated.username,
            subject=updated.subject,
        )

    # New user — create it
    user = await user_store.create_user(req)
    logger.info(f"Register: new user created id={user.id}")
    token = create_access_token(user.id, user.role)
    return AuthResponse(
        access_token=token,
        token_type="bearer",
        role=user.role,
        username=user.username,
        subject=user.subject,
    )


@router.get("/me")
async def get_me():
    """Returns current user info when a valid token is provided in Authorization header."""
    return {"detail": "Valid token — auth middleware passed"}


@router.get("/users", response_model=list[UserInDB])
async def list_users():
    return await user_store.list_users()