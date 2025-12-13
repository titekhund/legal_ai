"""
Authentication service for user management, JWT tokens, and usage tracking
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_logger, get_settings
from app.db.models import User, UsageRecord

logger = get_logger(__name__)
settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================================================
# Pydantic Schemas
# ============================================================================


class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response (without password)"""
    id: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    daily_requests_count: int
    daily_requests_remaining: int
    monthly_requests_count: int
    monthly_requests_remaining: int
    total_requests_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class UsageInfo(BaseModel):
    """Schema for usage information"""
    daily_used: int
    daily_limit: int
    daily_remaining: int
    monthly_used: int
    monthly_limit: int
    monthly_remaining: int
    total_used: int
    daily_resets_at: datetime
    monthly_resets_at: datetime


# ============================================================================
# Password Utilities
# ============================================================================


def hash_password(password: str) -> str:
    """Hash a plain text password"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================================
# JWT Utilities
# ============================================================================


def create_access_token(user_id: str, email: str) -> tuple[str, datetime]:
    """
    Create a JWT access token

    Returns:
        Tuple of (token, expiration_datetime)
    """
    expires_at = datetime.utcnow() + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    to_encode = {
        "sub": user_id,
        "email": email,
        "exp": expires_at,
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return token, expires_at


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT access token

    Returns:
        Token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError as e:
        logger.debug(f"JWT decode error: {e}")
        return None


# ============================================================================
# Auth Service Class
# ============================================================================


class AuthService:
    """Service for user authentication and management"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def register_user(self, user_data: UserCreate) -> User:
        """
        Register a new user

        Args:
            user_data: User registration data

        Returns:
            Created user

        Raises:
            ValueError: If email already exists
        """
        # Check if email exists
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise ValueError("Email already registered")

        # Create user
        user = User(
            email=user_data.email.lower(),
            password_hash=hash_password(user_data.password),
            full_name=user_data.full_name,
            is_active=True,
            is_verified=True,  # Auto-verify for now
            daily_requests_reset_at=datetime.utcnow(),
            monthly_requests_reset_at=datetime.utcnow(),
        )

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        logger.info(f"User registered: {user.email}")
        return user

    async def authenticate_user(
        self, email: str, password: str
    ) -> Optional[User]:
        """
        Authenticate a user by email and password

        Returns:
            User if authenticated, None otherwise
        """
        user = await self.get_user_by_email(email)
        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        if not user.is_active:
            return None

        # Update last login
        user.last_login_at = datetime.utcnow()
        await self.session.commit()

        return user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        result = await self.session.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""

        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def reset_usage_counters(self, user: User) -> None:
        """Reset usage counters if the reset period has passed"""
        now = datetime.utcnow()

        # Reset daily counter if a day has passed
        if (now - user.daily_requests_reset_at).days >= 1:
            user.daily_requests_count = 0
            user.daily_requests_reset_at = now
            logger.info(f"Daily counter reset for user {user.email}")

        # Reset monthly counter if a month has passed
        if (now - user.monthly_requests_reset_at).days >= 30:
            user.monthly_requests_count = 0
            user.monthly_requests_reset_at = now
            logger.info(f"Monthly counter reset for user {user.email}")

        await self.session.commit()

    async def check_usage_limit(self, user: User) -> tuple[bool, str]:
        """
        Check if user has exceeded usage limits (non-atomic, use for display only)

        Returns:
            Tuple of (is_allowed, reason_if_not_allowed)
        """
        # Reset counters if needed
        await self.reset_usage_counters(user)

        # Check daily limit
        if user.daily_requests_count >= settings.daily_request_limit:
            return False, "Daily request limit reached"

        # Check monthly limit
        if user.monthly_requests_count >= settings.monthly_request_limit:
            return False, "Monthly request limit reached"

        return True, ""

    async def check_and_increment_usage(
        self,
        user_id: str,
        endpoint: str,
        request_type: str = "chat",
        tokens_used: Optional[int] = None,
        processing_time_ms: Optional[int] = None,
    ) -> tuple[bool, str, Optional[User]]:
        """
        Atomically check usage limits and increment if allowed.
        Uses SELECT FOR UPDATE to prevent race conditions.

        Returns:
            Tuple of (is_allowed, reason_if_not_allowed, updated_user)
        """

        now = datetime.utcnow()

        # Lock the user row for update (prevents concurrent modifications)
        result = await self.session.execute(
            select(User)
            .where(User.id == user_id)
            .with_for_update()
        )
        user = result.scalar_one_or_none()

        if not user:
            return False, "User not found", None

        # Reset daily counter if a day has passed
        if (now - user.daily_requests_reset_at).days >= 1:
            user.daily_requests_count = 0
            user.daily_requests_reset_at = now
            logger.info(f"Daily counter reset for user {user.email}")

        # Reset monthly counter if a month has passed
        if (now - user.monthly_requests_reset_at).days >= 30:
            user.monthly_requests_count = 0
            user.monthly_requests_reset_at = now
            logger.info(f"Monthly counter reset for user {user.email}")

        # Check daily limit
        if user.daily_requests_count >= settings.daily_request_limit:
            await self.session.commit()  # Release lock
            return False, "Daily request limit reached", user

        # Check monthly limit
        if user.monthly_requests_count >= settings.monthly_request_limit:
            await self.session.commit()  # Release lock
            return False, "Monthly request limit reached", user

        # Increment counters (within the lock)
        user.daily_requests_count += 1
        user.monthly_requests_count += 1
        user.total_requests_count += 1

        # Create usage record
        usage_record = UsageRecord(
            user_id=user.id,
            endpoint=endpoint,
            request_type=request_type,
            tokens_used=tokens_used,
            processing_time_ms=processing_time_ms,
        )
        self.session.add(usage_record)

        await self.session.commit()
        logger.debug(
            f"Usage atomically incremented for {user.email}: "
            f"daily={user.daily_requests_count}, monthly={user.monthly_requests_count}"
        )

        return True, "", user

    async def increment_usage(
        self,
        user: User,
        endpoint: str,
        request_type: str = "chat",
        tokens_used: Optional[int] = None,
        processing_time_ms: Optional[int] = None,
    ) -> None:
        """
        Increment user's usage counters and record the request.
        DEPRECATED: Use check_and_increment_usage for atomic operations.
        """
        # Reset counters if needed
        await self.reset_usage_counters(user)

        # Increment counters
        user.daily_requests_count += 1
        user.monthly_requests_count += 1
        user.total_requests_count += 1

        # Create usage record
        usage_record = UsageRecord(
            user_id=user.id,
            endpoint=endpoint,
            request_type=request_type,
            tokens_used=tokens_used,
            processing_time_ms=processing_time_ms,
        )
        self.session.add(usage_record)

        await self.session.commit()
        logger.debug(
            f"Usage incremented for {user.email}: "
            f"daily={user.daily_requests_count}, monthly={user.monthly_requests_count}"
        )

    def get_usage_info(self, user: User) -> UsageInfo:
        """Get user's usage information"""
        daily_remaining = max(0, settings.daily_request_limit - user.daily_requests_count)
        monthly_remaining = max(0, settings.monthly_request_limit - user.monthly_requests_count)

        return UsageInfo(
            daily_used=user.daily_requests_count,
            daily_limit=settings.daily_request_limit,
            daily_remaining=daily_remaining,
            monthly_used=user.monthly_requests_count,
            monthly_limit=settings.monthly_request_limit,
            monthly_remaining=monthly_remaining,
            total_used=user.total_requests_count,
            daily_resets_at=user.daily_requests_reset_at + timedelta(days=1),
            monthly_resets_at=user.monthly_requests_reset_at + timedelta(days=30),
        )

    def user_to_response(self, user: User) -> UserResponse:
        """Convert User model to UserResponse"""
        daily_remaining = max(0, settings.daily_request_limit - user.daily_requests_count)
        monthly_remaining = max(0, settings.monthly_request_limit - user.monthly_requests_count)

        return UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            daily_requests_count=user.daily_requests_count,
            daily_requests_remaining=daily_remaining,
            monthly_requests_count=user.monthly_requests_count,
            monthly_requests_remaining=monthly_remaining,
            total_requests_count=user.total_requests_count,
            created_at=user.created_at,
        )

    async def login(self, login_data: UserLogin) -> Optional[TokenResponse]:
        """
        Authenticate user and return JWT token

        Returns:
            TokenResponse if authenticated, None otherwise
        """
        user = await self.authenticate_user(login_data.email, login_data.password)
        if not user:
            return None

        token, expires_at = create_access_token(str(user.id), user.email)
        expires_in = int((expires_at - datetime.utcnow()).total_seconds())

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=expires_in,
            user=self.user_to_response(user),
        )
