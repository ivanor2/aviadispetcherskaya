# tests/test_airport.py
import pytest
from fastapi import status
from app.db.session import get_session
from sqlmodel import Session, select
from app.models.airport import Airport


def test_create_airport_by_admin(client, admin_headers, sample_airport_data):
    """Тестирует создание аэропорта администратором."""
    response = client.post("/airports", json=sample_airport_data, headers=admin_headers)

    if response.status_code != status.HTTP_201_CREATED:
        print(f"Create airport failed: {response.status_code} - {response.text}")

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()

    assert data["icao_code"] == sample_airport_data["icaoCode"].upper()
    assert data["name"] == sample_airport_data["name"]


def test_get_airport_by_id(client, admin_headers, sample_airport_data):
    """Тестирует получение аэропорта по ID."""

    create_response = client.post("/airports", json=sample_airport_data, headers=admin_headers)
    assert create_response.status_code == 201
    airport_id = create_response.json()["id"]


    response = client.get(f"/airports/{airport_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["id"] == airport_id
    assert data["icao_code"] == sample_airport_data["icaoCode"].upper()


def test_get_airports_paginated(client, regular_user_headers):
    """Тестирует получение списка аэропортов с пагинацией."""
    response = client.get("/airports", headers=regular_user_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_update_airport_by_admin(client, admin_headers, sample_airport_data):
    """Тестирует обновление аэропорта администратором (PUT /airports/{id})."""

    create_response = client.post("/airports", json=sample_airport_data, headers=admin_headers)
    assert create_response.status_code == 201
    airport_id = create_response.json()["id"]

    updated_name = "New Updated Airport Name"
    update_data = {"icaoCode": sample_airport_data["icaoCode"], "name": updated_name}

    response = client.put(f"/airports/{airport_id}", json=update_data, headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["name"] == updated_name


def test_delete_airport_by_admin(client, admin_headers, sample_airport_data, session):
    """Тестирует удаление аэропорта администратором (DELETE /airports/{id})."""
    create_response = client.post("/airports", json=sample_airport_data, headers=admin_headers)
    assert create_response.status_code == 201
    airport_id = create_response.json()["id"]

    response = client.delete(f"/airports/{airport_id}", headers=admin_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    deleted_airport = session.get(Airport, airport_id)
    assert deleted_airport is None

def test_create_airport_forbidden_for_guest(client, regular_user_headers, sample_airport_data):
    """Тестирует, что гость не может создать аэропорт (POST)."""
    response = client.post("/airports", json=sample_airport_data, headers=regular_user_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_airport_forbidden_for_guest(client, admin_headers, regular_user_headers, sample_airport_data):
    """Тестирует, что гость не может обновить аэропорт (PUT)."""
    create_response = client.post("/airports", json=sample_airport_data, headers=admin_headers)
    airport_id = create_response.json()["id"]

    update_data = {"icaoCode": sample_airport_data["icaoCode"], "name": "Unauthorized Update"}

    response = client.put(f"/airports/{airport_id}", json=update_data, headers=regular_user_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_delete_airport_forbidden_for_guest(client, admin_headers, regular_user_headers, sample_airport_data):
    """Тестирует, что гость не может удалить аэропорт (DELETE)."""
    create_response = client.post("/airports", json=sample_airport_data, headers=admin_headers)
    airport_id = create_response.json()["id"]

    response = client.delete(f"/airports/{airport_id}", headers=regular_user_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_get_airport_by_icao(client, admin_headers, sample_airport_data):
    create_response = client.post("/airports", json=sample_airport_data, headers=admin_headers)
    assert create_response.status_code == 201
    icao = create_response.json()["icao_code"]

    response = client.get(f"/airports/by-icao/{icao}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["icao_code"] == icao


def test_create_airport_duplicate_icao(client, admin_headers, sample_airport_data):
    # Первое создание
    res1 = client.post("/airports", json=sample_airport_data, headers=admin_headers)
    assert res1.status_code == 201

    # Повторное создание с тем же ICAO → 400
    res2 = client.post("/airports", json=sample_airport_data, headers=admin_headers)
    assert res2.status_code == 400
    assert "уже существует" in res2.json()["detail"]


def test_update_airport_nonexistent(client, admin_headers):
    update_data = {"name": "Updated Name"}
    response = client.put("/airports/999999", json=update_data, headers=admin_headers)
    assert response.status_code == 404


def test_delete_airport_nonexistent(client, admin_headers):
    response = client.delete("/airports/999999", headers=admin_headers)
    assert response.status_code == 404