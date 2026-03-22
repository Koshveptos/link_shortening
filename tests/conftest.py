
import pytest
import pytest_asyncio
import os
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from src.main import app
from src.db.session import get_session
from src.models.base import Base


from src.models.user import User  # noqa: F401
from src.models.links import Link  # noqa: F401
from src.models.click_events import ClickEvent  # noqa: F401



TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://shortener_admin:admin@localhost:5434/shortener_load_test"
)

engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
    pool_pre_ping=True,  
)

TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="function")
async def db():
    """Асинхронная сессия для тестов"""

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    

    async with TestingSessionLocal() as session:
        yield session
    

    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE click_events, links, users RESTART IDENTITY CASCADE;"))


@pytest_asyncio.fixture(scope="function")
async def client(db: AsyncSession):
    """AsyncClient с оверрайдом асинхронной сессии"""
    
    async def override_get_session():
        yield db
    
    app.dependency_overrides[get_session] = override_get_session
    

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    
    app.dependency_overrides.clear()