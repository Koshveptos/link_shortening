# 🔗 Link Shortening Service

Сервис для сокращения длинных ссылок с аналитикой переходов, кастомными алиасами и авторизацией пользователей.

> 🎓 Учебный проект для курса по Python/FastAPI

---

## 🚀 Быстрый старт

### Требования
- Docker Engine 24+
- Docker Compose v2+
- Или локально: Python 3.13+, uv

### Запуск через Docker (рекомендуется)

```bash
# 1. Клонируй репозиторий
git clone https://github.com/Koshveptos/link_shortening.git
cd link_shortening

# 2. Настрой окружение
cp .env.example .env

# 🔹 Сгенерируй SECRET_KEY (мин. 32 символа):
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 🔹 Отредактируй .env: вставь ключ и при необходимости смени пароли

# 3. Запусти сервисы
docker compose up -d --build

# 4. Подожди ~30 секунд (healthchecks)

# 5. Примени миграции (только при первом запуске!)
docker compose exec app alembic upgrade head

# 6. Проверь работу
curl http://127.0.0.1:8000/health
# Ответ: {"status":"ok","app":"LinkShortener"} ✅
```

### Запуск локально (для разработки)

```bash
# 1. Установи зависимости
uv sync

# 2. Настрой окружение
cp .env.example .env
# 🔹 Отредактируй .env по необходимости

# 3. Запусти БД и Redis через Docker
docker compose up -d postgres redis

# 4. Примени миграции
uv run alembic upgrade head

# 5. Запусти приложение
uv run uvicorn src.main:app --reload --host 127.0.0.1 --port 8000

# 6. Открой в браузере:
#    📚 Документация: http://127.0.0.1:8000/docs
#    💚 Health: http://127.0.0.1:8000/health
```

---

## ⚙️ Настройка окружения (.env)

Файл `.env.example` содержит шаблон переменных окружения:

```env
# 🔐 Security
SECRET_KEY=your-super-secret-key-min-32-chars-here  # ← ОБЯЗАТЕЛЬНО замени!
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# 👤 PostgreSQL
POSTGRES_USER=shortener_admin
POSTGRES_PASSWORD=admin
POSTGRES_DB=shortener
POSTGRES_PORT=5433

# 🔗 Redis
REDIS_URL=redis://localhost:6380/0  # Для локального запуска

# 📊 App
APP_NAME=LinkShortener
DEBUG=True
LOG_LEVEL=INFO

# 🔧 pgAdmin (опционально)
PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=admin
```

### Как настроить:

1. Скопируй шаблон:
   ```bash
   cp .env.example .env
   ```

2. Открой `.env` в редакторе и замени:
   - `SECRET_KEY` → сгенерируй новый:
     ```bash
     python -c "import secrets; print(secrets.token_urlsafe(32))"
     ```
   - Пароли для БД (если хочешь изменить дефолтные)



## 🗄️ Применение миграций (Alembic)

Миграции применяются **только один раз** при первом запуске:

```bash
# В Docker:
docker compose exec app alembic upgrade head

# Локально:
uv run alembic upgrade head
```

### Полезные команды Alembic:

```bash
# Проверить статус миграций
alembic current

# Создать новую миграцию после изменения моделей
alembic revision --autogenerate -m "description"

# Откатить последнюю миграцию
alembic downgrade -1

# Просмотреть историю
alembic history
```


---

# TODO

В данной версии есть несколько недочетов, у меня не вышло интеграционне тесторование из-за проблем с фикциями и бдшкой, тестирование проводилось вручную, в будущем написать тесты
+регистрация есть, но есть поля для управления администратором(его пока что нет) так де сделать профиль для администратора
+расширить аналитику, не успел дописать тулзу для получения доп данных по редиректу для сбора аналитики - таблица есть, расчеты есть - данные не все)))

## 📡 Описание API

### 🔐 Авторизация

| Метод | Эндпоинт | Описание | Доступ |
|-------|----------|----------|--------|
| `POST` | `/api/auth/register` | Регистрация пользователя | Публичный |
| `POST` | `/api/auth/login` | Получение JWT токена | Публичный |
| `GET`  | `/api/auth/me` | Данные текущего пользователя | Авторизованный |


### 🔗 Ссылки

| Метод | Эндпоинт | Описание | Доступ |
|-------|----------|----------|--------|
| `POST` | `/api/links/shorten` | Создать короткую ссылку | Публичный |
| `GET`  | `/api/links/{code}` | Редирект на оригинал | Публичный |
| `GET`  | `/api/links/{code}/info` | Информация о ссылке |  Владелец |
| `PATCH`| `/api/links/{code}` | Обновить ссылку |  Владелец |
| `DELETE`| `/api/links/{code}` | Удалить ссылку |  Владелец |
| `GET`  | `/api/links/{code}/stats` | Статистика переходов |  Владелец |
| `GET`  | `/api/links/search` | Поиск по оригинальному URL | Публичный |


## 🗄️ Структура базы данных

### Таблицы

#### `users`
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | INTEGER | Primary key |
| `username` | VARCHAR(50) | Уникальное имя пользователя |
| `email` | VARCHAR(255) | Уникальный email |
| `password_hash` | VARCHAR(255) | Хэш пароля (bcrypt) |
| `created_at` | TIMESTAMP | Дата регистрации |
| `is_active` | BOOLEAN | Статус аккаунта |
| `last_login_at` | TIMESTAMP | Последний вход |

#### `links`
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | INTEGER | Primary key |
| `user_id` | INTEGER | Владелец ссылки (nullable) |
| `short_code` | VARCHAR(12) | Сгенерированный короткий код |
| `custom_alias` | VARCHAR(50) | Пользовательский алиас (nullable) |
| `original_url` | VARCHAR(2048) | Исходный URL |
| `created_at` | TIMESTAMP | Дата создания |
| `expires_at` | TIMESTAMP | Срок жизни (nullable) |
| `last_clicked_at` | TIMESTAMP | Последний клик |
| `is_active` | BOOLEAN | Статус ссылки |
| `clicks_count` | INTEGER | Счётчик переходов |

#### `click_events`
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | INTEGER | Primary key |
| `link_id` | INTEGER | Ссылка (foreign key) |
| `ip_address` | VARCHAR(45) | IP пользователя |
| `country_code` | VARCHAR(2) | Код страны (GeoIP) |
| `device_type` | VARCHAR(20) | Тип устройства |
| `created_at` | TIMESTAMP | Время клика |

### Индексы
- `ix_links_short_code`, `ix_links_custom_alias` — быстрый поиск по коду
- `ix_links_user_id`, `ix_links_created_at` — фильтрация по пользователю/дате
- `ix_click_events_link_id`, `ix_click_events_created_at` — аналитика

---

## 🗑️ Очистка и перезапуск

```bash
# Остановить сервисы (сохраняя данные)
docker compose down

# Остановить и удалить ВСЕ данные (осторожно!)
docker compose down -v

# Пересобрать образы
docker compose up -d --build

# Посмотреть логи
docker compose logs -f app      # приложение
docker compose logs -f postgres # база данных
docker compose logs -f redis    # кэш
```

---





## 🧪 Тестирование
Проект покрыт тестами: юнит-тесты, интеграционные и нагрузочные.  
![img\locust.png](img\pocritie_unit_inter.png)

Результаты нагрузочного тестирования
![img\locust.png](img\locust.png)

Подробные отчеты лежат в папках img и htmcov
Выводу по тестированию - по нагрузочному сервер начал себя чувствовать при 1200 пользователях и rump up 20, что говорит либо об ограничениях тестирования на локальном устройстве, либо о недостаточной оптимизации бд (падал с 500 или 0 статусом)
насчет юнит и интеграционного - покрытие 87%

### Юнит-тесты ()
```bash
#  Запустить все юнит-тесты
uv run pytest tests/unit/ -v

# Запустить с покрытием
uv run coverage run -m pytest tests/unit/
uv run coverage report -m

# Сгенерировать HTML-отчёт
uv run coverage html
Start-Process htmlcov/index.html
```
### Интеграционные тесты и нагрузочные

Проверяют API-эндпоинты через AsyncClient с реальной PostgreSQL базой.

**Подготовка:**

```bash
#для начала создай
# .env.loadtest — для нагрузочных тестов 


SECRET_KEY=test-secret-key-for-load-testing-only-min-32-chars-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256


POSTGRES_USER=shortener_admin
POSTGRES_PASSWORD=admin
POSTGRES_DB=shortener_load_test
POSTGRES_PORT=5434           


DATABASE_URL=postgresql+asyncpg://shortener_admin:admin@postgres:5432/shortener_load_test
REDIS_URL=redis://redis:6379/1 


APP_NAME=LinkShortener-LoadTest
DEBUG=True
LOG_LEVEL=WARNING

```




```bash
# 1. Запусти тестовый стек Docker (если ещё не запущен)
docker compose -f docker-compose.loadtest.yml up -d

# 2. Создай тестовую БД (один раз)
docker compose -f docker-compose.loadtest.yml exec postgres psql -U shortener_admin -d postgres -c "CREATE DATABASE shortener_load_test;"

# 3. Примени миграции
docker compose -f docker-compose.loadtest.yml exec app alembic upgrade head

# 4. Проверь, что app работает
curl http://127.0.0.1:8001/health

#  Запустить все интеграционные тесты
uv run pytest tests/integration_test/ -v


#  Запустить с покрытием
uv run coverage run -m pytest tests/integration_test/
uv run coverage report -m

# 5. Запусти Locust 
uv run locust -f tests/load/locustfile.py --host http://127.0.0.1:8001

# 6. Очисти после тестов
docker compose -f docker-compose.loadtest.yml down -v


###если падает с проблемой нет бд *500 то проверь Таблицы
# Проверь, что БД существует:
docker compose -f docker-compose.loadtest.yml exec postgres psql -U shortener_admin -d postgres -c "\l"

# Если нет shortener_load_test — создай:
docker compose -f docker-compose.loadtest.yml exec postgres psql -U shortener_admin -d postgres -c "CREATE DATABASE shortener_load_test;"

# Примени миграции:
docker compose -f docker-compose.loadtest.yml exec app alembic upgrade head
```

---

## 🐳 Docker-контейнеры

| Сервис | Порт | Описание |
|--------|------|----------|
| `app` | 127.0.0.1:8000 | FastAPI приложение |
| `postgres` | 127.0.0.1:5433 | PostgreSQL 16 |
| `redis` | 127.0.0.1:6379 | Redis для кэширования |
| `pgadmin` | 127.0.0.1:5050 | Веб-интерфейс для БД (опционально) |

> 🔐 Все порты привязаны только к `127.0.0.1` для безопасности.

---

## 🛠️ Технологии

- **Backend**: FastAPI, SQLAlchemy (async), Pydantic v2
- **БД**: PostgreSQL 16 + Alembic миграции
- **Кэш**: Redis (редиректы, статистика)
- **Авторизация**: JWT (HS256), bcrypt
- **Тесты**: pytest, pytest-asyncio
- **Контейнеризация**: Docker, Docker Compose
- **Линтеры**: ruff, mypy, pre-commit

---

## 📄 Лицензия

MIT License. См. файл `LICENSE`.
