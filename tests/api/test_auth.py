# tests/api/test_auth.py
"""
Тесты для проверки функциональности аутентификации и авторизации.

Проверяет:
- Регистрацию новых пользователей
- Вход в систему (login)
- Обработку неверных учётных данных
- Контроль доступа на основе ролей (RBAC)
"""
import pytest
from fastapi import status


def test_register_and_login(client):
    """
    Тестирует полный цикл регистрации и входа пользователя.
    
    Проверяет:
    1. Успешную регистрацию нового пользователя (статус 201)
    2. Успешный вход с корректными учётными данными (статус 200)
    3. Наличие access_token в ответе на login
    
    Args:
        client: Тестовый HTTP клиент.
    """
    reg = client.post("/api/v1/auth/register", json={"username": "new_user", "password": "Pass1234!"})
    assert reg.status_code == status.HTTP_201_CREATED

    login = client.post("/api/v1/auth/login", json={"username": "new_user", "password": "Pass1234!"})
    assert login.status_code == status.HTTP_200_OK
    assert "access_token" in login.json()


def test_invalid_password(client):
    """
    Тестирует отказ во входе при неверном пароле.
    
    Проверяет, что попытка входа с неправильным паролем
    возвращает статус 401 UNAUTHORIZED.
    
    Args:
        client: Тестовый HTTP клиент.
    """
    client.post("/api/v1/auth/register", json={"username": "u2", "password": "Pass1234!"})
    res = client.post("/api/v1/auth/login", json={"username": "u2", "password": "Wrong!"})
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


def test_role_based_access(client, guest_token):
    """
    Тестирует контроль доступа на основе ролей (RBAC).
    
    Проверяет, что пользователь с ролью "guest" не может
    создавать аэропорты (требуется роль admin/dispatcher).
    
    Args:
        client: Тестовый HTTP клиент.
        guest_token: JWT токен пользователя с ролью guest.
    """
    headers = {"Authorization": f"Bearer {guest_token}"}
    # Гость не должен создавать аэропорты
    res = client.post("/api/v1/airports", json={"icaoCode": "UUWW", "name": "Test"}, headers=headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN

def test():
    pass