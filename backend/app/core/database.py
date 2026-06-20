"""
ATELIX ViralClip AI Pipeline — Database Configuration
Async SQLAlchemy engine + session management.
Supports PostgreSQL (production) and SQLite (testing).
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

_connect_args = {}
_pool_config = {
    "pool_size": 20,
    "max_overflow": 10,
    "pool_pre_ping": True,
}

if "sqlite" in settings.database_url:
    _connect_args = {"check_same_thread": False}
    _pool_config = {"pool_size": 0, "max_overflow": -1}

engine = create_async_engine(
    settings.database_url,
    connect_args=_connect_args,
    echo=settings.app_debug,
    **_pool_config,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    await engine.dispose()
