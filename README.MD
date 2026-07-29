# Chat Volc Backend

REST API для чат-приложения на FastAPI: пользователи, приватные чаты, сообщения, JWT-авторизация (email/пароль и OAuth Яндекс/ВК).

## Стек

| Компонент | Роль |
|-----------|------|
| **FastAPI** | HTTP API, OpenAPI/Swagger |
| **SQLAlchemy** | ORM и работа с БД |
| **Pydantic** | Валидация запросов/ответов |
| **Alembic** | Миграции схемы БД |
| **PostgreSQL** | Основная БД в Docker |
| **SQLite** | БД по умолчанию локально / в тестах |
| **Redis** | Кэш/сессии (клиент готов через `get_redis`) |
| **Uvicorn** | ASGI-сервер |
| **Docker Compose** | Запуск app + postgres + redis |
| **pytest** | Unit/integration-тесты |

## Структура проекта

```
chat_volc_backend/
├── main.py                 # Точка входа FastAPI, CORS, роутеры, health-check
├── requirements.txt        # Python-зависимости
├── pytest.ini              # Конфиг pytest
├── alembic.ini             # Конфиг Alembic
├── .env.example            # Пример переменных окружения
│
├── chat_volc/              # Основной пакет приложения
│   ├── settings.py         # DATABASE_URL, REDIS_URL, engine, get_db, get_redis
│   ├── auth.py             # JWT, хеш паролей, OAuth-профили, get_current_user
│   ├── models/
│   │   ├── models.py       # ORM: User, PrivateChat, Message
│   │   └── schemas.py      # Pydantic-схемы запросов/ответов
│   └── routers/
│       ├── auth.py         # /auth — регистрация, логин, OAuth, /me
│       ├── users.py        # /users — поиск, чаты пользователя, CRUD
│       ├── chats.py        # /private_chat — создание/получение/удаление чатов
│       └── messages.py     # /private_chat/{id}/message — сообщения
│
├── alembic/                # Миграции БД
│   ├── env.py              # Берёт DATABASE_URL из settings
│   └── versions/           # Ревизии схемы
│
├── tests/                  # Тесты API и моделей
│   ├── conftest.py         # In-memory SQLite + TestClient
│   └── test_*.py
│
├── Dockerfile              # Образ приложения
├── docker-compose.yml      # Сервисы: app, postgres, redis
├── docker-entrypoint.sh    # alembic upgrade + uvicorn
├── docker.sh               # start | stop | restart | status
├── run.sh                  # Локальный uvicorn без Docker
└── migrate.sh              # alembic upgrade head
```

## Компоненты и ответственность

### Приложение

| Файл / модуль | За что отвечает |
|---------------|-----------------|
| `main.py` | Создаёт `FastAPI`-приложение, CORS, подключает роутеры, эндпоинт `/healf_check`, Swagger на `/docs` |
| `chat_volc/settings.py` | URL БД и Redis из env, SQLAlchemy engine/сессии, `get_db()`, `get_redis()` |
| `chat_volc/auth.py` | JWT (выпуск/проверка), bcrypt-хеш паролей, OAuth (Яндекс/ВК), зависимость `get_current_user` |
| `chat_volc/models/models.py` | Таблицы `users`, `private_chats`, `messages`; логика создания чата/сообщения |
| `chat_volc/models/schemas.py` | Контракты API: auth, users, chats, messages |

### API-роутеры

| Роутер | Префикс | За что отвечает |
|--------|---------|-----------------|
| `routers/auth.py` | `/auth` | `register`, `login`, `oauth`, `dev` (dev-логин), `me` |
| `routers/users.py` | `/users` | Поиск пользователей, список чатов по uid, создание/получение/удаление |
| `routers/chats.py` | `/private_chat` | Создание чата по uid двух пользователей, get/delete, все сообщения чата |
| `routers/messages.py` | `/private_chat/{id}` | Создание/получение/удаление сообщения |

### Docker

| Файл | За что отвечает |
|------|-----------------|
| `Dockerfile` | Сборка образа Python-приложения |
| `docker-compose.yml` | Оркестрация **app** (API :8080), **postgres** (:5432), **redis** (:6379) |
| `docker-entrypoint.sh` | При старте контейнера: миграции → запуск uvicorn |
| `docker.sh` | Удобный CLI: `start` / `stop` / `restart` / `status` |
| `.dockerignore` | Что не копировать в образ |

### Миграции и скрипты

| Файл | За что отвечает |
|------|-----------------|
| `alembic/` | История и применение схемы БД |
| `migrate.sh` | `alembic upgrade head` |
| `run.sh` | Локальный запуск API без Docker (`uvicorn` на :8080) |

### Тесты

| Файл | За что отвечает |
|------|-----------------|
| `tests/conftest.py` | Фикстуры: in-memory БД, TestClient, пользователи/чат |
| `tests/test_*.py` | Покрытие health, auth, users, chats, messages, models, validation |

## Быстрый старт (Docker)

```bash
cp .env.example .env   # при необходимости
./docker.sh start
```

- API: http://127.0.0.1:8080  
- Swagger: http://127.0.0.1:8080/docs  

Остановка:

```bash
./docker.sh stop
```

## Локальный запуск без Docker

```bash
python -m venv env
source env/bin/activate
pip install -r requirements.txt
./migrate.sh          # или alembic upgrade head
./run.sh              # uvicorn на :8080
```

По умолчанию без `DATABASE_URL` используется SQLite (`./test.db`).

## Переменные окружения

См. `.env.example`:

| Переменная | Назначение |
|------------|------------|
| `APP_PORT` | Порт API на хосте (по умолчанию 8080) |
| `DATABASE_URL` | Строка подключения к БД |
| `REDIS_URL` | Строка подключения к Redis |
| `POSTGRES_*` | Учётка/БД PostgreSQL в Compose |
| `JWT_SECRET` | Секрет подписи JWT |
| `JWT_EXPIRE_DAYS` | Срок жизни токена |
| `ALLOW_DEV_AUTH` | Разрешить `/auth/dev` (для разработки) |

## Тесты

```bash
./env/bin/pytest -v
./env/bin/pytest --cov=chat_volc --cov=main --cov-report=term-missing
```

## Миграции

```bash
alembic revision --autogenerate -m "описание"
alembic upgrade head
```
