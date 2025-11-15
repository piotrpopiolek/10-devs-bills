from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
from src.db.models import *
from src.config import Config
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

   # Convert postgresql:// to postgresql+asyncpg://
database_url = settings.DATABASE_URL.replace(
       "postgresql://", "postgresql+asyncpg://", 1
)

engine = create_async_engine(
    Config.DATABASE_URL,
    echo=True # Set to True for debugging, False for production
)

async def init_db():
    """
    Initialize the database.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncSession:
    Session = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with Session() as session:
        yield session