from sqlmodel import SQLModel, create_engine, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from config import settings

# Async engine for runtime operations
async_engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Sync engine for migrations / init
sync_engine = create_engine(
    settings.sync_database_url,
    echo=False,
)


async def init_db():
    """Create all tables if they don't exist."""
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


def get_sync_session():
    from sqlalchemy.orm import sessionmaker

    sync_session = sessionmaker(sync_engine, expire_on_commit=False)
    return sync_session()
