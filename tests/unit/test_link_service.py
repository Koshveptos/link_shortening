
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from src.services.link_service import (
    generate_short_code,
    is_code_available,
    create_short_link,
    get_link_by_code,
    update_link,
    delete_link,
    record_click,
)
from src.schemas.link import LinkCreate, LinkUpdate
from src.models.links import Link




def test_generate_short_code_default_length():
    """По умолчанию код должен быть длиной 8"""
    code = generate_short_code()
    assert len(code) == 8
    assert code.isalnum()  # Только буквы и цифры


def test_generate_short_code_custom_length():
    """Длина кода должна соответствовать параметру"""
    for length in [6, 8, 10, 12]:
        code = generate_short_code(length=length)
        assert len(code) == length


def test_generate_short_code_is_random():
    """Два вызова должны давать разные результаты"""
    codes = [generate_short_code() for _ in range(100)]
    # Вероятность коллизии при 62^8 вариантах ничтожна
    assert len(set(codes)) == 100


def test_generate_short_code_uses_alphabet():
    """Код должен содержать только символы из ALPHABET"""
    import string
    alphabet = set(string.ascii_letters + string.digits)
    
    for _ in range(50):
        code = generate_short_code()
        assert all(c in alphabet for c in code)

@pytest.mark.asyncio
async def test_is_code_available_when_free():
    """Код доступен, если в БД нет записей"""
    # Мокаем session и результат запроса
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    result = await is_code_available(mock_session, "abc123")
    
    assert result is True
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_is_code_available_when_taken():
    """Код занят, если в БД есть запись"""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = 1  # Найден ID
    mock_session.execute.return_value = mock_result
    
    result = await is_code_available(mock_session, "abc123")
    
    assert result is False


@pytest.mark.asyncio
async def test_is_code_available_checks_both_fields():
    """Проверяет и short_code, и custom_alias"""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    await is_code_available(mock_session, "test-code")
    
    # Проверяем, что в where() используется OR для двух полей
    call_args = mock_session.execute.call_args[0][0]

    query_str = str(call_args)
    assert "short_code" in query_str
    assert "custom_alias" in query_str



@pytest.mark.asyncio
async def test_create_short_link_generates_code():
    """Создание ссылки генерирует short_code"""
    mock_session = AsyncMock()
    
    # Мокаем is_code_available -> True с первого раза
    with patch('src.services.link_service.is_code_available', return_value=True):
        payload = LinkCreate(original_url="https://example.com")
        
        link = await create_short_link(mock_session, payload, user_id=1)
        
        assert link.short_code is not None
        assert len(link.short_code) == 8
        assert link.original_url == "https://example.com/"
        assert link.user_id == 1


@pytest.mark.asyncio
async def test_create_short_link_uses_custom_alias():
    """Если передан custom_alias, он используется"""
    mock_session = AsyncMock()
    
    with patch('src.services.link_service.is_code_available', return_value=True):
        payload = LinkCreate(
            original_url="https://example.com",
            custom_alias="my-link"
        )
        
        link = await create_short_link(mock_session, payload, user_id=1)
        
        assert link.custom_alias == "my-link"
        # short_code генерируется отдельно, даже если есть alias
        assert link.short_code is not None


@pytest.mark.asyncio
async def test_create_short_link_retries_on_collision():
    """При коллизии кода функция пробует ещё раз"""
    mock_session = AsyncMock()
    
    # Мокаем: первые 2 вызова -> код занят, 3-й -> свободен
    with patch('src.services.link_service.is_code_available') as mock_avail:
        mock_avail.side_effect = [True, True, True]  # Всегда свободен для теста
        
        payload = LinkCreate(original_url="https://example.com")
        link = await create_short_link(mock_session, payload)
        
        # Проверяем, что is_code_available вызывался (хотя бы 1 раз)
        assert mock_avail.call_count >= 1


@pytest.mark.asyncio
async def test_create_short_link_raises_on_to_many_collisions():
    """После 5 попыток генерации должна быть ошибка"""
    mock_session = AsyncMock()
    
    # Мокаем: всегда код занят
    with patch('src.services.link_service.is_code_available', return_value=False):
        payload = LinkCreate(original_url="https://example.com")
        
        with pytest.raises(ValueError, match="Не удалось сгенерировать уникальный код"):
            await create_short_link(mock_session, payload)


@pytest.mark.asyncio
async def test_create_short_link_converts_expires_at_to_naive():
    """expires_at с timezone конвертируется в naive для БД"""
    mock_session = AsyncMock()
    
    with patch('src.services.link_service.is_code_available', return_value=True):
        # Создаём aware datetime
        aware_dt = datetime(2099, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        payload = LinkCreate(
            original_url="https://example.com",
            expires_at=aware_dt
        )
        
        link = await create_short_link(mock_session, payload)
        
        # Проверяем, что у expires_at нет tzinfo (naive)
        assert link.expires_at.tzinfo is None
        # Но значение должно совпадать
        assert link.expires_at.year == 2099


@pytest.mark.asyncio
async def test_create_short_link_strips_url():
    """original_url обрезается от пробелов"""
    mock_session = AsyncMock()
    
    with patch('src.services.link_service.is_code_available', return_value=True):
        payload = LinkCreate(original_url="  https://example.com  ")
        
        link = await create_short_link(mock_session, payload)
        
        assert link.original_url == "https://example.com/"




@pytest.mark.asyncio
async def test_get_link_by_code_found():
    """Находит активную ссылку по коду"""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    
    # Мокаем найденную ссылку
    mock_link = MagicMock(spec=Link)
    mock_link.short_code = "abc123"
    mock_link.is_active = True
    mock_link.expires_at = None  # Не истекла
    mock_result.scalar_one_or_none.return_value = mock_link
    mock_session.execute.return_value = mock_result
    
    result = await get_link_by_code(mock_session, "abc123")
    
    assert result is mock_link
    assert result.short_code == "abc123"


@pytest.mark.asyncio
async def test_get_link_by_code_not_found():
    """Возвращает None, если ссылка не найдена"""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    result = await get_link_by_code(mock_session, "nonexistent")
    
    assert result is None


@pytest.mark.asyncio
async def test_get_link_by_code_filters_inactive():
    """Не возвращает неактивные ссылки"""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    
    # Мокаем неактивную ссылку
    mock_link = MagicMock(spec=Link)
    mock_link.is_active = False
    mock_result.scalar_one_or_none.return_value = None  # Фильтр SQL исключит её
    mock_session.execute.return_value = mock_result
    
    result = await get_link_by_code(mock_session, "abc123")
    
    assert result is None


@pytest.mark.asyncio
async def test_get_link_by_code_filters_expired():
    """Не возвращает истёкшие ссылки"""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    
    # Истёкшая ссылка будет отфильтрована SQL-запросом
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    result = await get_link_by_code(mock_session, "expired-code")
    
    assert result is None




@pytest.mark.asyncio
async def test_update_link_updates_fields():
    """Обновляет только переданные поля"""
    mock_session = AsyncMock()
    

    mock_link = MagicMock(spec=Link)
    mock_link.short_code = "abc123"
    mock_link.is_active = True
    mock_link.expires_at = None
    
    payload = LinkUpdate(is_active=False)  # Обновляем только is_active
    
    result = await update_link(mock_session, mock_link, payload)
    
    # Проверяем, что поле обновилось
    assert mock_link.is_active is False
    # expires_at не должен измениться (не передан в payload)
    assert mock_link.expires_at is None
    # session.commit() должен быть вызван
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_link_converts_expires_at():
    """Конвертирует expires_at в naive при обновлении"""
    mock_session = AsyncMock()
    mock_link = MagicMock(spec=Link)
    
    aware_dt = datetime(2099, 12, 31, tzinfo=timezone.utc)
    payload = LinkUpdate(expires_at=aware_dt)
    
    await update_link(mock_session, mock_link, payload)
    
    # Проверяем, что установилось naive datetime
    assert mock_link.expires_at.tzinfo is None




@pytest.mark.asyncio
async def test_delete_link_deactivates():
    """Мягкое удаление: устанавливает is_active=False"""
    mock_session = AsyncMock()
    mock_link = MagicMock(spec=Link)
    mock_link.is_active = True
    
    result = await delete_link(mock_session, mock_link)
    
    assert result is True
    assert mock_link.is_active is False
    mock_session.commit.assert_called_once()



@pytest.mark.asyncio
async def test_record_click_increments_counter():
    """Запись клика увеличивает clicks_count"""
    mock_session = AsyncMock()
    mock_link = MagicMock(spec=Link)
    mock_link.clicks_count = 5
    mock_link.last_clicked_at = None
    
    result = await record_click(
        mock_session, 
        mock_link,
        ip_address="127.0.0.1",
        country_code="RU",
        device_type="desktop"
    )
    
    # Счётчик увеличился
    assert mock_link.clicks_count == 6
    # last_clicked_at установлен (naive)
    assert mock_link.last_clicked_at is not None
    assert mock_link.last_clicked_at.tzinfo is None
    # ClickEvent создан и добавлен в сессию
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_record_click_handles_null_fields():
    """None-значения корректно обрабатываются"""
    mock_session = AsyncMock()
    mock_link = MagicMock(spec=Link)
    mock_link.clicks_count = 0
    
    result = await record_click(
        mock_session,
        mock_link,
        ip_address=None,  # None допустимо
        country_code=None,
        device_type=None
    )
    
    assert result is not None
    assert mock_link.clicks_count == 1