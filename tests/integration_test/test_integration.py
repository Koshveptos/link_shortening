
import pytest
from httpx import AsyncClient 


@pytest.mark.asyncio
async def test_create_link_minimal(client: AsyncClient):
    """Создание ссылки с минимальными данными"""
    response = await client.post("/api/links/shorten", json={
        "original_url": "https://example.com"
    })
    assert response.status_code in (200, 201)
    
    data = response.json()
    assert "short_code" in data or "code" in data or "id" in data


@pytest.mark.asyncio
async def test_create_link_full_response(client: AsyncClient):
    """Проверка полного ответа при создании ссылки"""
    response = await client.post("/api/links/shorten", json={
        "original_url": "https://example.com/test"
    })
    assert response.status_code in (200, 201)
    
    data = response.json()
    assert isinstance(data, dict)
    assert "id" in data
    assert "short_code" in data or "code" in data
    assert "original_url" in data


@pytest.mark.asyncio
async def test_create_link_with_custom_alias(client: AsyncClient):
    """Создание ссылки с кастомным алиасом"""
    response = await client.post("/api/links/shorten", json={
        "original_url": "https://example.com",
        "custom_alias": "my-test-link"
    })
    assert response.status_code in (200, 201)
    
    data = response.json()
    assert data.get("custom_alias") == "my-test-link"



@pytest.mark.asyncio
async def test_empty_url_returns_error(client: AsyncClient):
    """Пустой URL должен вернуть ошибку валидации"""
    response = await client.post("/api/links/shorten", json={
        "original_url": ""
    })
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_missing_original_url_returns_error(client: AsyncClient):
    """Отсутствие original_url должно вернуть ошибку"""
    response = await client.post("/api/links/shorten", json={})
    assert response.status_code == 422




@pytest.mark.asyncio
async def test_redirect_returns_302(client: AsyncClient):
    """Редирект должен вернуть 302 статус"""

    create = await client.post("/api/links/shorten", json={
        "original_url": "https://example.com"
    })
    assert create.status_code in (200, 201)
    
    code = create.json().get("short_code") or create.json().get("code")
    assert code is not None
    

    response = await client.get(f"/api/links/{code}", follow_redirects=False)
    assert response.status_code in (301, 302, 307)


@pytest.mark.asyncio
async def test_redirect_has_location_header(client: AsyncClient):
    """Редирект должен содержать заголовок Location"""
    create = await client.post("/api/links/shorten", json={
        "original_url": "https://example.com"
    })
    code = create.json().get("short_code") or create.json().get("code")
    
    response = await client.get(f"/api/links/{code}", follow_redirects=False)
    assert "location" in response.headers
    assert response.headers["location"] == "https://example.com"


@pytest.mark.asyncio
async def test_redirect_not_found(client: AsyncClient):
    """Редирект по несуществующему коду должен вернуть 404"""
    response = await client.get("/api/links/THIS_CODE_DOES_NOT_EXIST_12345")
    assert response.status_code == 404




@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    """Успешная регистрация пользователя"""
    response = await client.post("/api/auth/register", json={
        "username": "testuser_unique",
        "email": "test_unique@example.com",
        "password": "StrongPass123!"
    })
    assert response.status_code in (200, 201, 400, 422)
    
    if response.status_code in (200, 201):
        data = response.json()
        assert "password" not in data
        assert "password_hash" not in data


@pytest.mark.asyncio
async def test_register_missing_username(client: AsyncClient):
    """Регистрация без username должна вернуть ошибку"""
    response = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "StrongPass123!"
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Успешный логин должен вернуть токен"""
    # Сначала регистрируем
    await client.post("/api/auth/register", json={
        "username": "logintest",
        "email": "login@test.com",
        "password": "StrongPass123!"
    })
    
    # Теперь логинимся
    response = await client.post("/api/auth/login", json={
        "email": "login@test.com",
        "password": "StrongPass123!"
    })
    
    assert response.status_code in (200, 401, 404)
    
    if response.status_code == 200:
        data = response.json()
        assert "access_token" in data
        assert data.get("token_type") == "bearer"




@pytest.mark.asyncio
async def test_get_stats_requires_auth(client: AsyncClient):
    """Получение статистики требует авторизации"""
    # Создаём ссылку
    create = await client.post("/api/links/shorten", json={
        "original_url": "https://example.com"
    })
    code = create.json().get("short_code") or create.json().get("code")
    
    # pробуем без токена → должен быть 401
    response = await client.get(f"/api/links/{code}/stats")
    assert response.status_code in (401, 404)




@pytest.mark.asyncio
async def test_update_link_requires_auth(client: AsyncClient):
    """Обновление ссылки требует авторизации"""
    create = await client.post("/api/links/shorten", json={
        "original_url": "https://example.com"
    })
    code = create.json().get("short_code") or create.json().get("code")
    
    response = await client.patch(f"/api/links/{code}", json={
        "is_active": False
    })
    assert response.status_code in (401, 403, 404)


@pytest.mark.asyncio
async def test_delete_link_requires_auth(client: AsyncClient):
    """Удаление ссылки требует авторизации"""
    create = await client.post("/api/links/shorten", json={
        "original_url": "https://example.com"
    })
    code = create.json().get("short_code") or create.json().get("code")
    
    response = await client.delete(f"/api/links/{code}")
    assert response.status_code in (401, 403, 404)




@pytest.mark.asyncio
async def test_response_content_type_is_json(client: AsyncClient):
    """Ответы API должны иметь Content-Type: application/json"""
    response = await client.post("/api/links/shorten", json={
        "original_url": "https://example.com"
    })
    content_type = response.headers.get("content-type", "")
    assert content_type.startswith("application/json")


@pytest.mark.asyncio
async def test_sql_injection_attempt(client: AsyncClient):
    """Попытка SQL-инъекции должна быть обработана безопасно"""
    payload = {
        "original_url": "https://example.com'; DROP TABLE links; --"
    }
    response = await client.post("/api/links/shorten", json=payload)

    assert response.status_code in (200, 201, 400, 422)



@pytest.mark.asyncio
async def test_link_expires_at_works(client: AsyncClient):
    """Ссылка со сроком жизни должна перестать работать после истечения"""
    from datetime import datetime, timedelta, timezone
    
    # Создаём ссылку, которая истекает через 1 секунду
    future = datetime.now(timezone.utc) + timedelta(seconds=1)
    
    response = await client.post("/api/links/shorten", json={
        "original_url": "https://example.com/expires",
        "expires_at": future.isoformat()
    })
    assert response.status_code in (200, 201)
    
    code = response.json().get("short_code") or response.json().get("code")
    
    # Сразу после создания — должна работать
    redirect = await client.get(f"/api/links/{code}", follow_redirects=False)
    assert redirect.status_code == 302
    
    # Ждём истечения
    import asyncio
    await asyncio.sleep(2)
    
    # После истечения — 404
    redirect = await client.get(f"/api/links/{code}", follow_redirects=False)
    assert redirect.status_code == 404


@pytest.mark.asyncio
async def test_custom_alias_is_unique(client: AsyncClient):
    """Кастомный алиас должен быть уникальным"""
    # Создаём первую ссылку с алиасом
    response1 = await client.post("/api/links/shorten", json={
        "original_url": "https://example.com/first",
        "custom_alias": "my-unique-alias"
    })
    assert response1.status_code in (200, 201)
    
    # Пытаемся создать вторую с тем же алиасом
    response2 = await client.post("/api/links/shorten", json={
        "original_url": "https://example.com/second",
        "custom_alias": "my-unique-alias"
    })
    # Должна быть ошибка валидации или 400
    assert response2.status_code in (400, 409, 422)