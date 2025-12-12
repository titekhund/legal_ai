"""
Authentication API endpoints
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_logger
from app.db import get_async_session, User
from app.services import (
    AuthService,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UsageInfo,
    decode_access_token,
)

logger = get_logger(__name__)
router = APIRouter()

# Security scheme for JWT
security = HTTPBearer(auto_error=False)


# ============================================================================
# Dependencies
# ============================================================================


async def get_auth_service(
    session: AsyncSession = Depends(get_async_session),
) -> AuthService:
    """Dependency to get auth service instance"""
    return AuthService(session)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    Raises 401 if not authenticated.
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_service = AuthService(session)
    user = await auth_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Email verification check (prepared for future use)
    # Currently auto-verified on registration, but infrastructure is ready
    # Uncomment below to require email verification:
    # if not user.is_verified:
    #     raise HTTPException(
    #         status_code=403,
    #         detail="Email not verified. Please check your email for verification link.",
    #     )

    return user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: AsyncSession = Depends(get_async_session),
) -> Optional[User]:
    """
    Dependency to get the current user if authenticated, None otherwise.
    Does not raise 401 - useful for endpoints that work with or without auth.
    """
    if not credentials:
        return None

    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    auth_service = AuthService(session)
    user = await auth_service.get_user_by_id(user_id)

    if not user or not user.is_active:
        return None

    return user


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/auth/register", response_model=TokenResponse)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Register a new user account

    - **email**: Valid email address (must be unique)
    - **password**: Password (min 6 characters recommended)
    - **full_name**: Optional full name

    Returns JWT token on successful registration.
    """
    # Validate password
    if len(user_data.password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters long"
        )

    try:
        user = await auth_service.register_user(user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Create token for auto-login after registration
    login_data = UserLogin(email=user_data.email, password=user_data.password)
    token_response = await auth_service.login(login_data)

    if not token_response:
        raise HTTPException(
            status_code=500,
            detail="Failed to create authentication token"
        )

    logger.info(f"User registered: {user.email}")
    return token_response


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Authenticate and get JWT token

    - **email**: Registered email address
    - **password**: Account password

    Returns JWT token on successful authentication.
    """
    token_response = await auth_service.login(login_data)

    if not token_response:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    logger.info(f"User logged in: {login_data.email}")
    return token_response


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Get current authenticated user information

    Requires valid JWT token in Authorization header.
    """
    # Reset counters if needed
    await auth_service.reset_usage_counters(current_user)
    return auth_service.user_to_response(current_user)


@router.get("/auth/usage", response_model=UsageInfo)
async def get_usage_info(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Get current user's usage information

    Returns daily and monthly request counts and limits.
    """
    # Reset counters if needed
    await auth_service.reset_usage_counters(current_user)
    return auth_service.get_usage_info(current_user)


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Refresh JWT token

    Returns a new JWT token with extended expiration.
    Requires valid (non-expired) token.
    """
    from app.services.auth_service import create_access_token
    from datetime import datetime, timezone

    token, expires_at = create_access_token(str(current_user.id), current_user.email)
    expires_in = int((expires_at - datetime.now(timezone.utc)).total_seconds())

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        user=auth_service.user_to_response(current_user),
    )


@router.post("/auth/logout")
async def logout():
    """
    Logout endpoint (informational)

    JWT tokens are stateless, so logout is handled client-side by
    removing the token. This endpoint exists for API completeness.
    """
    return {"message": "Successfully logged out. Please remove your token."}
