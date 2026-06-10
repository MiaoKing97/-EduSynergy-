"""
Auth middleware: extract Bearer token from Authorization header,
populate `request.state.user` if valid.
"""
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..auth.token import decode_access_token

security = HTTPBearer(auto_error=False)


async def get_current_user(request: Request) -> dict:
    """Dependency: attaches user info to request.state if authenticated."""
    credentials = await security(request)
    if not credentials:
        return None

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    request.state.user = {
        "user_id": payload.sub,
        "role": payload.role,
    }
    return request.state.user
