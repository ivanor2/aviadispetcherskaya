# tests/test_auth.py
import pytest
from fastapi import status
from app.schemas.user_schema import UserCreate, UserLogin, TokenResponse
from app.models.user import User
from app.db.session import get_session
from sqlmodel import Session, select

def test_register_new_user(client, regular_user_data):
    """Тестирует регистрацию нового пользователя."""
    response = client.post("/auth/register", json=regular_user_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == regular_user_data["username"]
    assert data["role"] == "guest"

def test_login_valid_user(client, regular_user_data):
    """Тестирует успешный логин зарегистрированного пользователя."""
    client.post("/auth/register", json=regular_user_data)

    login_data = {
        "username": regular_user_data["username"],
        "password": regular_user_data["password"]
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["tokenType"] == "bearer"

def test_login_invalid_credentials(client, regular_user_data):
    """Тестирует логин с неверными учетными данными."""
    client.post("/auth/register", json=regular_user_data)

    login_data = {
        "username": regular_user_data["username"],
        "password": "wrongpassword123!"
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_current_user_authenticated(client, regular_user_data):
    """Тестирует получение данных текущего пользователя с валидным токеном."""
    client.post("/auth/register", json=regular_user_data)
    login_response = client.post("/auth/login", json={
        "username": regular_user_data["username"],
        "password": regular_user_data["password"]
    })
    access_token = login_response.json().get("access_token")

    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == regular_user_data["username"]

def test_change_user_role_by_admin(client, admin_headers, regular_user_data):
    """Тестирует изменение роли пользователя администратором."""
    reg_response = client.post("/auth/register", json=regular_user_data)
    assert reg_response.status_code == status.HTTP_201_CREATED
    user_id = reg_response.json()["id"]

    new_role_value = "dispatcher"

    response = client.put(f"/auth/{user_id}/role",
                          json={"role": new_role_value},
                          headers=admin_headers)

    assert response.status_code == status.HTTP_200_OK, f"Expected 200, got {response.status_code}. Response: {response.text}"

    data = response.json()
    assert data["role"] == new_role_value
    assert data["id"] == user_id

def test_register_duplicate_username(client, regular_user_data):
    client.post("/auth/register", json=regular_user_data)
    response = client.post("/auth/register", json=regular_user_data)
    assert response.status_code == 400
    assert "уже существует" in response.json()["detail"]


def test_login_missing_fields(client):
    response = client.post("/auth/login", json={"username": "test"})
    assert response.status_code == 422  # Pydantic validation


def test_get_me_unauthorized(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_logout_clears_cookie(client, regular_user_data):
    client.post("/auth/register", json=regular_user_data)
    login_resp = client.post("/auth/login", json=regular_user_data)
    assert "set-cookie" in login_resp.headers

    logout_resp = client.post("/auth/logout")
    assert logout_resp.status_code == 200
    assert "set-cookie" in logout_resp.headers  # должен быть delete_cookie


def test_get_all_users_requires_admin(client, regular_user_headers):
    response = client.get("/auth/users", headers=regular_user_headers)
    assert response.status_code == 403


def test_get_all_users_by_admin(client, admin_headers, regular_user_data):
    # Создаём второго юзера
    client.post("/auth/register", json=regular_user_data)

    response = client.get("/auth/users", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 2  # admin + guest