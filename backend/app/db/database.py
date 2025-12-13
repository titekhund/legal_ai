"""
Database connection and session management
"""
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core import get_logger, get_settings

logger = get_logger(__name__)
settings = get_settings()

# Global engine and session factory
_engine = None
AsyncSessionLocal: Optional[async_sessionmaker] = None


async def init_db() -> None:
    """
    Initialize database connection and create tables
    """
    global _engine, AsyncSessionLocal

    database_url = settings.database_url
    if not database_url:
        logger.warning("DATABASE_URL not set, using SQLite fallback")
        database_url = "sqlite+aiosqlite:///./legal_ai.db"
    elif database_url.startswith("postgres://"):
        # Fix for asyncpg which requires postgresql+asyncpg://
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    logger.info(f"Connecting to database...")

    # Create async engine
    _engine = create_async_engine(
        database_url,
        echo=settings.is_development(),
        poolclass=NullPool if "sqlite" in database_url else None,
    )

    # Create session factory
    AsyncSessionLocal = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    # Create tables
    from app.db.models import Base
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized successfully")


async def close_db() -> None:
    """
    Close database connection
    """
    global _engine, AsyncSessionLocal

    if _engine:
        await _engine.dispose()
        _engine = None
        AsyncSessionLocal = None
        logger.info("Database connection closed")


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session
    """
    if not AsyncSessionLocal:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
