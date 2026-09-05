from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,
)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with async_session_maker() as session:
        yield session


async def init_db() -> None:
    if engine.url.drivername != "postgresql+asyncpg":
        raise RuntimeError("Autonomous QA Agent requires PostgreSQL via asyncpg")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
