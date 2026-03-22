# tests/conftest.py
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

# 🔹 Импортируй модели ДО использования Base!
from src.models.user import User  # noqa: F401
from src.models.links import Link  # noqa: F401
from src.models.click_events import ClickEvent  # noqa: F401

# 🔹 Бери URL из env или используй дефолт для тестов
# При запуске тестов задай TEST_DATABASE_URL или используй .env.loadtest
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://shortener_admin:admin@localhost:5434/shortener_load_test"
)

engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
    pool_pre_ping=True,  # Проверяет соединение перед использованием
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
    # 🔹 Создаём таблицы (если нет)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 🔹 Возвращаем сессию
    async with TestingSessionLocal() as session:
        yield session
    
    # 🔹 Очищаем данные после теста (но не удаляем таблицы)
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE click_events, links, users RESTART IDENTITY CASCADE;"))


@pytest_asyncio.fixture(scope="function")
async def client(db: AsyncSession):
    """AsyncClient с оверрайдом асинхронной сессии"""
    
    async def override_get_session():
        yield db
    
    app.dependency_overrides[get_session] = override_get_session
    
    # 🔹 AsyncClient для асинхронных запросов
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    
    app.dependency_overrides.clear()