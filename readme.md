# Airport Dispatcher API

REST API для АРМ диспетчера аэропорта.

## Назначение

Данный API предоставляет интерфейс для управления данными, связанными с авиарейсами, пассажирами и бронированием билетов. Он позволяет регистрировать пассажиров, управлять информацией о рейсах, продавать и отменять билеты, а также обеспечивает аутентификацию и авторизацию пользователей.

## Технологии

- **Язык программирования:** Python
- **Фреймворк:** [FastAPI](https://fastapi.tiangolo.com/)
- **ORM:** [SQLModel](https://sqlmodel.tiangolo.com/)
- **База данных:** PostgreSQL (через `postgresql+psycopg2`)
- **Аутентификация:** JWT (OAuth2 Password Bearer)
- **Хеширование паролей:** `passlib` с `argon2`
- **Пагинация:** `fastapi-pagination`
- **Документация:** Swagger UI ( `/api/v1/docs` ), ReDoc ( `/api/v1/redoc` )

## Установка зависимостей

1.  Убедитесь, что у вас установлен Python 3.8+.
2.  Рекомендуется создать виртуальное окружение:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # или
    # venv\Scripts\activate # Windows
    ```
3.  Установите зависимости:
    ```bash
    pip install -r requirements.txt
    ```

## Настройка базы данных и переменных окружения

1.  Установите и запустите PostgreSQL.
2.  Создайте базу данных (например, `airport_db`).
3.  Создайте файл `.env` в корне проекта и укажите свои параметры подключения к базе данных и секретный ключ:

    ```env
    DATABASE_URL=postgresql+psycopg2://<DB_USER>:<DB_PASSWORD>@<DB_HOST>:<DB_PORT>/<DB_NAME>
    SECRET_KEY=your-super-secret-and-long-key-change-in-production
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    ```

    *Пример:*
    ```env
    DATABASE_URL=postgresql+psycopg2://postgres:mysecretpassword@localhost:5432/airport_db
    SECRET_KEY=8a7c1f9e0b4d6f2a1c5e8f7a9b3c4d6e0f2a1c5e8f7a9b3c4d6e0f2a1c5e8f7a
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    ```

    **ВАЖНО:** Файл `.env` не должен быть закоммичен в репозиторий. Убедитесь, что он присутствует в `.gitignore`.

## Запуск приложения

После настройки базы данных и переменных окружения, запустите приложение с помощью Uvicorn:

```bash
uvicorn app.main:main_app --reload