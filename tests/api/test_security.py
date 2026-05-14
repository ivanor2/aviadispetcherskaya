# tests/api/test_security.py
"""
Тесты для проверки функций безопасности и работы с токенами.

Проверяет:
- Хеширование и верификацию паролей
- Создание и декодирование JWT токенов (access/refresh)
- Обработку невалидных и истёкших токенов
- Проверку ролей пользователей (admin_required, dispatcher_or_higher)
"""
import pytest
from fastapi import HTTPException, status
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
    get_current_user, admin_required, dispatcher_or_higher
)
from app.models.user import User


def test_hash_and_verify_password():
    """
    Тестирует функции хеширования и верификации паролей.
    
    Проверяет:
    1. Пароль хешируется (хееш не равен исходному паролю)
    2. Корректный пароль проходит верификацию
    3. Некорректный пароль не проходит верификацию
    """
    password = "MySecureP@ss123"
    hashed = hash_password(password)

    assert hashed != password  # Пароль захеширован
    assert verify_password(password, hashed)  # Проверка проходит
    assert not verify_password("WrongPassword", hashed)  # Неправильный пароль не проходит


def test_create_and_decode_access_token():
    """
    Тестирует создание и декодирование access токена.
    
    Проверяет:
    1. Успешное создание токена
    2. Корректное извлечение данных (sub) из токена
    """
    data = {"sub": "testuser", "role": "admin"}
    token = create_access_token(data)

    assert token is not None
    username = decode_token(token, expected_type="access")
    assert username == "testuser"


def test_decode_wrong_token_type():
    """
    Тестирует обработку токена неправильного типа.
    
    Проверяет, что попытка декодировать access-токен как refresh
    вызывает HTTPException со статусом 401.
    """
    access_token = create_access_token({"sub": "user"})

    # Пытаемся декодировать access-токен как refresh
    with pytest.raises(HTTPException) as exc:
        decode_token(access_token, expected_type="refresh")
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_decode_expired_token():
    """
    Тестирует обработку истёкшего токена.
    
    Создаёт токен с отрицательным временем жизни (уже истёкший)
    и проверяет, что decode_token возвращает None.
    """
    from datetime import timedelta
    # Создаём токен с истёкшим сроком
    token = create_access_token({"sub": "user"}, expires_delta=timedelta(seconds=-1))

    result = decode_token(token)
    assert result is None  # Истёкший токен не декодируется


def test_decode_invalid_token():
    """
    Тестирует обработку невалидного токена.
    
    Проверяет, что декодирование строки, не являющейся JWT,
    возвращает None.
    """
    result = decode_token("invalid.token.here")
    assert result is None


def test_get_current_user_invalid_token(db_session):
    """
    Тестирует получение текущего пользователя с невалидным токеном.
    
    Проверяет, что передача некорректного токена в get_current_user
    вызывает HTTPException со статусом 401.
    
    Args:
        db_session: Сессия базы данных.
    """
    from fastapi import Depends

    with pytest.raises(HTTPException) as exc:
        get_current_user(token="invalid_token", session=db_session)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_admin_required_non_admin(db_session):
    """
    Тестирует декоратор admin_required для пользователя без роли admin.
    
    Создаёт пользователя с ролью "guest" и проверяет, что
    admin_required вызывает HTTPException со статусом 403.
    
    Args:
        db_session: Сессия базы данных.
    """
    user = User(username="guest_user", password=hash_password("pass"), role="guest")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": user.username})

    with pytest.raises(HTTPException) as exc:
        admin_required(user=get_current_user(token=token, session=db_session))
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN


def test_dispatcher_or_higher_guest_denied(db_session):
    """
    Тестирует декоратор dispatcher_or_higher для пользователя с ролью guest.
    
    Проверяет, что пользователь с ролью "guest" не проходит проверку
    и получает HTTPException со статусом 403.
    
    Args:
        db_session: Сессия базы данных.
    """
    user = User(username="guest", password=hash_password("pass"), role="guest")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": user.username})

    with pytest.raises(HTTPException) as exc:
        dispatcher_or_higher(user=get_current_user(token=token, session=db_session))
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN


def test_dispatcher_or_higher_dispatcher_allowed(db_session):
    """
    Тестирует декоратор dispatcher_or_higher для пользователя с ролью dispatcher.
    
    Проверяет, что пользователь с ролью "dispatcher" успешно проходит проверку.
    
    Args:
        db_session: Сессия базы данных.
        
    Returns:
        Asserts: Проверяет, что возвращённый пользователь имеет роль dispatcher.
    """
    user = User(username="dispatch", password=hash_password("pass"), role="dispatcher")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": user.username})
    result = dispatcher_or_higher(user=get_current_user(token=token, session=db_session))

    assert result.role == "dispatcher"