
import pytest
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError

from src.schemas.link import LinkCreate, LinkUpdate, LinkOut


def test_link_create_valid_url():
    """Валидный URL проходит валидацию"""
    payload = LinkCreate(original_url="https://example.com")
    assert str(payload.original_url) == "https://example.com/"


def test_link_create_invalid_url():
    """Невалидный URL отклоняется"""
    with pytest.raises(ValidationError):
        LinkCreate(original_url="not-a-url")


def test_link_create_url_too_long():
    """URL длиннее 2048 символов отклоняется"""
    long_url = "https://example.com/" + "a" * 3000
    with pytest.raises(ValidationError):
        LinkCreate(original_url=long_url)


def test_link_create_custom_alias_valid():
    """Валидный custom_alias проходит"""
    payload = LinkCreate(
        original_url="https://example.com",
        custom_alias="my-link-123"
    )
    assert payload.custom_alias == "my-link-123"


def test_link_create_custom_alias_too_short():
    """alias короче 3 символов отклоняется"""
    with pytest.raises(ValidationError):
        LinkCreate(
            original_url="https://example.com",
            custom_alias="ab"  # 2 символа
        )


def test_link_create_custom_alias_too_long():
    """alias длиннее 50 символов отклоняется"""
    with pytest.raises(ValidationError):
        LinkCreate(
            original_url="https://example.com",
            custom_alias="a" * 51
        )


def test_link_create_custom_alias_invalid_chars():
    """alias с недопустимыми символами отклоняется"""
    with pytest.raises(ValidationError):
        LinkCreate(
            original_url="https://example.com",
            custom_alias="my link!"  # пробел и ! недопустимы
        )


def test_link_create_expires_at_future():
    """expires_at в будущем проходит"""
    future = datetime.now(timezone.utc) + timedelta(days=30)
    payload = LinkCreate(
        original_url="https://example.com",
        expires_at=future
    )
    assert payload.expires_at == future


def test_link_create_expires_at_past():
    """expires_at в прошлом отклоняется"""
    past = datetime.now(timezone.utc) - timedelta(days=1)
    with pytest.raises(ValidationError, match="время должно быть в будущем"):
        LinkCreate(
            original_url="https://example.com",
            expires_at=past
        )


def test_link_create_optional_fields():
    """Необязательные поля могут отсутствовать"""
    payload = LinkCreate(original_url="https://example.com")
    assert payload.custom_alias is None
    assert payload.expires_at is None




def test_link_update_partial():
    """Можно обновлять только часть полей"""
    payload = LinkUpdate(is_active=False)
    assert payload.is_active is False
    assert payload.expires_at is None
    assert payload.custom_alias is None


def test_link_update_custom_alias_valid():
    """Валидный alias в обновлении проходит"""
    payload = LinkUpdate(custom_alias="new-alias")
    assert payload.custom_alias == "new-alias"


def test_link_update_custom_alias_invalid():
    """Невалидный alias в обновлении отклоняется"""
    with pytest.raises(ValidationError):
        LinkUpdate(custom_alias="bad alias!")




def test_link_out_from_orm():
    """LinkOut создаётся из ORM-объекта (from_attributes=True)"""
    # Мокаем ORM-объект
    mock_link = type('MockLink', (), {
        'id': 1,
        'short_code': 'abc123',
        'custom_alias': 'my-link',
        'original_url': 'https://example.com',
        'created_at': datetime.now(),
        'expires_at': None,
        'is_active': True,
        'clicks_count': 42,
        'user_id': 1,
    })()
    
    output = LinkOut.model_validate(mock_link)
    
    assert output.id == 1
    assert output.short_code == 'abc123'
    assert output.clicks_count == 42
    # Проверяем, что пароль не попал в ответ (если бы был)
    assert not hasattr(output, 'password_hash')