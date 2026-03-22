# tests/test_passenger.py
import pytest
from fastapi import status
from app.db.session import get_session
from sqlmodel import Session, select
from app.models.passenger import Passenger


def test_create_passenger_by_dispatcher(client, admin_headers, sample_passenger_data):
    # admin может, т.к. он >= dispatcher (dispatcher_or_higher)
    response = client.post("/passengers", json=sample_passenger_data, headers=admin_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["fullName"] == sample_passenger_data["fullName"]


def test_create_passenger_duplicate_passport(client, admin_headers, sample_passenger_data):
    client.post("/passengers", json=sample_passenger_data, headers=admin_headers)
    response = client.post("/passengers", json=sample_passenger_data, headers=admin_headers)
    assert response.status_code == 400
    assert "уже зарегистрирован" in response.json()["detail"]


def test_get_passenger_by_id(client, admin_headers, sample_passenger_data):
    create_resp = client.post("/passengers", json=sample_passenger_data, headers=admin_headers)
    passenger_id = create_resp.json()["id"]

    response = client.get(f"/passengers/{passenger_id}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["id"] == passenger_id


def test_search_passenger_by_passport(client, admin_headers, sample_passenger_data):
    create_resp = client.post("/passengers", json=sample_passenger_data, headers=admin_headers)
    passport = create_resp.json()["passport_number"]

    response = client.get(f"/passengers/search/by-passport/{passport}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["passport_number"] == passport


def test_search_passengers_by_name(client, admin_headers, sample_passenger_data):
    sample_passenger_data["fullName"] = "Иван Иванов Иванович"
    client.post("/passengers", json=sample_passenger_data, headers=admin_headers)

    response = client.get("/passengers/search/by-name/Иванов", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "Иванов" in data[0]["fullName"]


def test_update_passenger_by_admin(client, admin_headers, sample_passenger_data):
    create_resp = client.post("/passengers", json=sample_passenger_data, headers=admin_headers)
    passenger_id = create_resp.json()["id"]

    update_data = {"fullName": "Обновлённое Имя"}
    response = client.put(f"/passengers/{passenger_id}", json=update_data, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["fullName"] == "Обновлённое Имя"


def test_delete_passenger_by_admin(client, admin_headers, sample_passenger_data):
    create_resp = client.post("/passengers", json=sample_passenger_data, headers=admin_headers)
    passenger_id = create_resp.json()["id"]

    response = client.delete(f"/passengers/{passenger_id}", headers=admin_headers)
    assert response.status_code == 204

    response = client.get(f"/passengers/{passenger_id}", headers=admin_headers)
    assert response.status_code == 404


# Права доступа:
def test_create_passenger_forbidden_for_guest(client, regular_user_headers, sample_passenger_data):
    response = client.post("/passengers", json=sample_passenger_data, headers=regular_user_headers)
    assert response.status_code == 403


def test_update_passenger_forbidden_for_guest(client, admin_headers, regular_user_headers, sample_passenger_data):
    create_resp = client.post("/passengers", json=sample_passenger_data, headers=admin_headers)
    passenger_id = create_resp.json()["id"]

    update_data = {"fullName": "Попытка обновления гостем"}
    response = client.put(f"/passengers/{passenger_id}", json=update_data, headers=regular_user_headers)
    assert response.status_code == 403


def test_get_passengers_paginated(client, admin_headers):
    response = client.get("/passengers", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data