# tests/unit/test_user_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from src.services.user_service import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    authenticate_user,
    update_last_login,
)
from src.schemas.user import UserCreate
from src.models.user import User


@pytest.mark.asyncio
async def test_create_user_success():
    """Успешное создание пользователя"""
    mock_session = AsyncMock()
    

    with patch('src.services.user_service.get_user_by_email', return_value=None):
        with patch('src.services.user_service.get_password_hash', return_value='hashed'):
            payload = UserCreate(
                username="testuser",
                email="test@example.com",
                password="StrongPass123!"
            )
            

            mock_user = MagicMock(spec=User)
            mock_user.id = 1
            mock_user.username = "testuser"
            mock_user.email = "test@example.com"
            
            # Мокаем session.add и commit
            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()
            

            with patch.object(User, '__init__', return_value=None):
                with patch('src.services.user_service.User', return_value=mock_user):
                    result = await create_user(mock_session, payload)
                    
                    assert result is mock_user
                    mock_session.add.assert_called_once()
                    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_user_duplicate_email():
    """Создание пользователя с занятым email"""
    mock_session = AsyncMock()
    

    existing_user = MagicMock(spec=User)
    
    with patch('src.services.user_service.get_user_by_email', return_value=existing_user):
        payload = UserCreate(
            username="testuser",
            email="test@example.com",
            password="StrongPass123!"
        )
        
        with pytest.raises(ValueError, match="Пользователь с такой почтой уже есть"):
            await create_user(mock_session, payload)


@pytest.mark.asyncio
async def test_get_user_by_email_found():
    """Поиск пользователя по найденному email"""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_user = MagicMock(spec=User)
    mock_user.email = "test@example.com"
    
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_result
    
    result = await get_user_by_email(mock_session, "test@example.com")
    
    assert result is mock_user
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_by_email_not_found():
    """Поиск пользователя по несуществующему email"""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    result = await get_user_by_email(mock_session, "notfound@example.com")
    
    assert result is None


@pytest.mark.asyncio
async def test_get_user_by_id_found():
    """Поиск пользователя по найденному ID"""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_user = MagicMock(spec=User)
    mock_user.id = 1
    
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_result
    
    result = await get_user_by_id(mock_session, 1)
    
    assert result is mock_user


@pytest.mark.asyncio
async def test_get_user_by_id_with_user_id_filter():
    """Поиск пользователя по ID с фильтром по владельцу"""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_user = MagicMock(spec=User)

    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_result
    

    result = await get_user_by_id(mock_session, user_id=1)
    
    assert result is mock_user
    # Опционально: проверь, что запрос был с фильтром
    assert mock_session.execute.called


@pytest.mark.asyncio
async def test_authenticate_user_success():
    """Успешная аутентификация"""
    mock_session = AsyncMock()
    mock_user = MagicMock(spec=User)
    mock_user.password_hash = "hashed_pass"
    
    with patch('src.services.user_service.get_user_by_email', return_value=mock_user):
        with patch('src.services.user_service.verify_password', return_value=True):
            result = await authenticate_user(mock_session, "test@example.com", "correct_pass")
            
            assert result is mock_user


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password():
    """Аутентификация с неверным паролем"""
    mock_session = AsyncMock()
    mock_user = MagicMock(spec=User)
    mock_user.password_hash = "hashed_pass"
    
    with patch('src.services.user_service.get_user_by_email', return_value=mock_user):
        with patch('src.services.user_service.verify_password', return_value=False):
            result = await authenticate_user(mock_session, "test@example.com", "wrong_pass")
            
            assert result is None


@pytest.mark.asyncio
async def test_authenticate_user_not_found():
    """Аутентификация несуществующего пользователя"""
    mock_session = AsyncMock()
    
    with patch('src.services.user_service.get_user_by_email', return_value=None):
        result = await authenticate_user(mock_session, "notfound@example.com", "any_pass")
        
        assert result is None


@pytest.mark.asyncio
async def test_update_last_login():
    """Обновление времени последнего входа"""
    mock_session = AsyncMock()
    mock_user = MagicMock(spec=User)
    
    await update_last_login(mock_session, mock_user)
    

    assert mock_user.last_login_at is not None
    assert mock_user.last_login_at.tzinfo is None
    mock_session.commit.assert_called_once()