"""
AI Video Clipper — Database Setup
===================================
SQLite database menggunakan SQLAlchemy async.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from loguru import logger

from config import settings

# ── Engine ──────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False},
)

# ── Session Factory ─────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Base Model ───────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Init DB ──────────────────────────────────────────────────
async def init_db():
    """Create all tables on startup."""
    import models  # noqa: F401 — ensure models are imported before create_all
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables created/verified")


# ── Dependency ───────────────────────────────────────────────
async def get_db():
    """FastAPI dependency untuk mendapatkan DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
