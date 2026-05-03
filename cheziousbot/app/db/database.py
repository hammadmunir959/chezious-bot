from pgvector.asyncpg import register_vector
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={
        "server_settings": {"search_path": "ai_agent, public"},
    },
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    from sqlmodel import SQLModel
    async with engine.begin() as conn:
        from app.models import __all__
        await conn.run_sync(SQLModel.metadata.create_all)
