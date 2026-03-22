# tests/test_flight.py
import pytest
from fastapi import status
from app.db.session import get_session
from sqlmodel import Session, select
from app.models.airport import Airport
from app.models.flight import Flight


def test_create_flight_by_admin(client, admin_headers, sample_flight_data):
    """Тестирует создание рейса администратором."""

    dep_airport_data = {"icaoCode": "EDDF", "name": "Frankfurt Airport"}
    arr_airport_data = {"icaoCode": "LEMD", "name": "Madrid Airport"}

    dep_resp = client.post("/airports", json=dep_airport_data, headers=admin_headers)
    arr_resp = client.post("/airports", json=arr_airport_data, headers=admin_headers)

    assert dep_resp.status_code == 201, f"Dep airport failed: {dep_resp.text}"
    assert arr_resp.status_code == 201, f"Arr airport failed: {arr_resp.text}"

    dep_id = dep_resp.json()["id"]
    arr_id = arr_resp.json()["id"]

    flight_data_with_ids = sample_flight_data.copy()
    flight_data_with_ids["departureAirportId"] = dep_id
    flight_data_with_ids["arrivalAirportId"] = arr_id

    response = client.post("/flights", json=flight_data_with_ids, headers=admin_headers)

    if response.status_code != status.HTTP_201_CREATED:
        print(f"Create flight failed: {response.status_code} - {response.text}")

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["flight_number"] == flight_data_with_ids["flightNumber"]
    assert data["departure_airport_id"] == dep_id
    assert data["arrival_airport_id"] == arr_id


def test_get_flights_paginated(client, regular_user_headers):
    """Тестирует получение списка рейсов с пагинацией."""
    response = client.get("/flights", headers=regular_user_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert "total" in data

def test_get_flight_by_id(client, regular_user_headers, admin_headers, sample_flight_data):
    # Подготавливаем аэропорты и рейс (как в create_flight_by_admin)
    dep_resp = client.post("/airports", json={"icaoCode": "UUWW", "name": "Domodedovo"}, headers=admin_headers)
    arr_resp = client.post("/airports", json={"icaoCode": "UUEE", "name": "Sheremetyevo"}, headers=admin_headers)
    dep_id, arr_id = dep_resp.json()["id"], arr_resp.json()["id"]

    flight_data = sample_flight_data.copy()
    flight_data.update({"departureAirportId": dep_id, "arrivalAirportId": arr_id})
    create_resp = client.post("/flights", json=flight_data, headers=admin_headers)
    assert create_resp.status_code == 201
    flight_id = create_resp.json()["id"]

    # Запрос по ID
    response = client.get(f"/flights/{flight_id}", headers=regular_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == flight_id
    assert data["flight_number"] == flight_data["flightNumber"]


def test_update_flight_by_admin(client, admin_headers, sample_flight_data):
    # Подготавливаем аэропорты
    dep_resp = client.post("/airports", json={"icaoCode": "EDDF", "name": "Frankfurt"}, headers=admin_headers)
    arr_resp = client.post("/airports", json={"icaoCode": "LFPG", "name": "Paris CDG"}, headers=admin_headers)
    dep_id, arr_id = dep_resp.json()["id"], arr_resp.json()["id"]

    flight_data = sample_flight_data.copy()
    flight_data.update({"departureAirportId": dep_id, "arrivalAirportId": arr_id})
    create_resp = client.post("/flights", json=flight_data, headers=admin_headers)
    flight_id = create_resp.json()["id"]

    # Обновляем
    update_payload = {"airlineName": "UpdatedAir"}
    response = client.put(f"/flights/{flight_id}", json=update_payload, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["airline_name"] == "UpdatedAir"


def test_delete_flight_by_admin(client, admin_headers, sample_flight_data):
    # Подготавливаем аэропорты и рейс
    dep_resp = client.post("/airports", json={"icaoCode": "UUOO", "name": "Omsk"}, headers=admin_headers)
    arr_resp = client.post("/airports", json={"icaoCode": "UNNT", "name": "Novosibirsk"}, headers=admin_headers)
    dep_id, arr_id = dep_resp.json()["id"], arr_resp.json()["id"]

    flight_data = sample_flight_data.copy()
    flight_data.update({"departureAirportId": dep_id, "arrivalAirportId": arr_id})
    create_resp = client.post("/flights", json=flight_data, headers=admin_headers)
    flight_id = create_resp.json()["id"]

    # Удаляем
    response = client.delete(f"/flights/{flight_id}", headers=admin_headers)
    assert response.status_code == 204

    # Проверяем, что в БД нет
    response = client.get(f"/flights/{flight_id}", headers=admin_headers)
    assert response.status_code == 404


def test_search_flights_by_arrival(client, regular_user_headers, admin_headers):
    # создаём аэропорт и рейс
    airport_resp = client.post("/airports", json={"icaoCode": "ZSPD", "name": "Shanghai Pudong"}, headers=admin_headers)
    arr_id = airport_resp.json()["id"]

    flight_data = {
        "flightNumber": "CA-123",
        "airlineName": "Air China",
        "departureAirportId": client.post("/airports", json={"icaoCode": "ZBAA", "name": "Beijing"}, headers=admin_headers).json()["id"],
        "arrivalAirportId": arr_id,
        "departureDate": "2025-12-20",
        "departureTime": "10:00:00",
        "totalSeats": 200,
        "freeSeats": 50
    }
    client.post("/flights", json=flight_data, headers=admin_headers)

    # ищем по части названия/ICAO
    response = client.get("/flights/search/by-arrival/Shanghai", headers=regular_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "Shanghai" in data[0]["flight_number"] or "Shanghai" in data[0]["arrival_airport_id"]  # лучше проверить через связь, но в JSON нет имён → можно расширить схему ответа


def test_get_flight_with_passengers(client, admin_headers, sample_flight_data, sample_passenger_data):
    # Подготавливаем аэропорты
    dep_id = client.post("/airports", json={"icaoCode": "UUWW", "name": "DME"}, headers=admin_headers).json()["id"]
    arr_id = client.post("/airports", json={"icaoCode": "UUEE", "name": "SVO"}, headers=admin_headers).json()["id"]

    # Создаём пассажира
    passenger_resp = client.post("/passengers", json=sample_passenger_data, headers=admin_headers)
    passenger_id = passenger_resp.json()["id"]

    # Создаём рейс
    flight_data = sample_flight_data.copy()
    flight_data.update({
        "departureAirportId": dep_id,
        "arrivalAirportId": arr_id,
        "flightNumber": "SU-111"
    })
    flight_resp = client.post("/flights", json=flight_data, headers=admin_headers)
    flight_number = flight_resp.json()["flight_number"]

    # Продаем билет
    booking_data = {"flightId": flight_resp.json()["id"], "passengerId": passenger_id}
    client.post("/bookings/", json=booking_data, headers=admin_headers)

    # Запрос по номеру рейса с пассажирами
    response = client.get(f"/flights/by-number/{flight_number}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["flight"]["flight_number"] == flight_number
    assert len(data["passengers"]) == 1
    assert data["passengers"][0]["fullName"] == sample_passenger_data["fullName"]


def test_delete_all_flights_requires_confirm(client, admin_headers):
    response = client.delete("/flights", headers=admin_headers)
    assert response.status_code == 400
    assert "Подтвердите удаление" in response.json()["detail"]

    response = client.delete("/flights?confirm=true", headers=admin_headers)
    assert response.status_code == 204