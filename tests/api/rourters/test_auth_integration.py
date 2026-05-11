import pytest
from fastapi import status


class TestAuthIntegration:
    def test_register_and_login_flow(self, client, fake_user_data):
        reg = client.post("/api/v2/auth/register", json=fake_user_data)
        assert reg.status_code == status.HTTP_201_CREATED

        login = client.post("/api/v2/auth/login", json=fake_user_data)
        assert login.status_code == status.HTTP_200_OK
        assert "access_token" in login.json()

    def test_login_invalid_creds(self, client, fake_user_data):
        client.post("/api/v2/auth/register", json=fake_user_data)
        login = client.post("/api/v2/auth/login", json={**fake_user_data, "password": "Wrong!"})
        assert login.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_me_unauthorized(self, client):
        assert client.get("/api/v2/auth/me").status_code == status.HTTP_401_UNAUTHORIZED

    def test_role_based_access_v2(self, client, guest_token, fake_airport_data):
        headers = {"Authorization": f"Bearer {guest_token}"}
        res = client.post("/api/v2/airports", json=fake_airport_data, headers=headers)
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_refresh_invalid_token(self, client):
        res = client.post("/api/v2/auth/refresh", params={"refresh_token": "invalid"})
        assert res.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_logout_clears_cookie(self, client, fake_user_data):
        client.post("/api/v2/auth/register", json=fake_user_data)
        login_res = client.post("/api/v2/auth/login", json=fake_user_data)
        assert login_res.status_code == 200

        logout_res = client.post("/api/v2/auth/logout")
        assert logout_res.status_code == 200