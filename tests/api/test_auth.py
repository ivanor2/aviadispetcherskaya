import pytest
from fastapi import status


def test_register_and_login(client):
    reg = client.post("/api/v1/auth/register", json={"username": "new_user", "password": "Pass1234!"})
    assert reg.status_code == status.HTTP_201_CREATED

    login = client.post("/api/v1/auth/login", json={"username": "new_user", "password": "Pass1234!"})
    assert login.status_code == status.HTTP_200_OK
    assert "access_token" in login.json()


def test_invalid_password(client):
    client.post("/api/v1/auth/register", json={"username": "u2", "password": "Pass1234!"})
    res = client.post("/api/v1/auth/login", json={"username": "u2", "password": "Wrong!"})
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


def test_role_based_access(client, guest_token):
    headers = {"Authorization": f"Bearer {guest_token}"}
    # Гость не должен создавать аэропорты
    res = client.post("/api/v1/airports", json={"icaoCode": "UUWW", "name": "Test"}, headers=headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN