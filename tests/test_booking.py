# tests/test_booking.py
import pytest
from fastapi import status
from app.db.session import get_session
from sqlmodel import Session, select
from app.models.booking import Booking
from app.models.flight import Flight
from tests.conftest import register_and_login_user

@pytest.fixture
def setup_flight_and_passenger(client, admin_headers, sample_flight_data, sample_passenger_data):
    # Аэропорты
    dep_id = client.post("/airports", json={"icaoCode": "UUWW", "name": "DME"}, headers=admin_headers).json()["id"]
    arr_id = client.post("/airports", json={"icaoCode": "UUEE", "name": "SVO"}, headers=admin_headers).json()["id"]

    # Пассажир
    passenger_resp = client.post("/passengers", json=sample_passenger_data, headers=admin_headers)
    passenger_id = passenger_resp.json()["id"]

    # Рейс
    flight_data = sample_flight_data.copy()
    flight_data.update({"departureAirportId": dep_id, "arrivalAirportId": arr_id})
    flight_resp = client.post("/flights", json=flight_data, headers=admin_headers)
    flight_id = flight_resp.json()["id"]

    return flight_id, passenger_id


def test_sell_ticket_by_dispatcher(client, admin_headers, setup_flight_and_passenger):
    flight_id, passenger_id = setup_flight_and_passenger

    booking_data = {"flightId": flight_id, "passengerId": passenger_id}
    response = client.post("/bookings/", json=booking_data, headers=admin_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["flightId"] == flight_id
    assert data["passengerId"] == passenger_id


def test_sell_ticket_duplicate(client, admin_headers, setup_flight_and_passenger):
    flight_id, passenger_id = setup_flight_and_passenger

    booking_data = {"flightId": flight_id, "passengerId": passenger_id}
    client.post("/bookings/", json=booking_data, headers=admin_headers)

    # Повторная продажа — 400
    response = client.post("/bookings/", json=booking_data, headers=admin_headers)
    assert response.status_code == 400
    assert "билет уже куплен" in response.json()["detail"]


def test_cancel_ticket_by_admin(client, admin_headers, setup_flight_and_passenger):
    flight_id, passenger_id = setup_flight_and_passenger

    booking_data = {"flightId": flight_id, "passengerId": passenger_id}
    create_resp = client.post("/bookings/", json=booking_data, headers=admin_headers)
    booking_id = create_resp.json()["id"]

    response = client.delete(f"/bookings/{booking_id}", headers=admin_headers)
    assert response.status_code == 204

    # Проверяем, что бронирование исчезло
    response = client.get(f"/bookings/by-passenger/{sample_passenger_data['passportNumber']}", headers=admin_headers)
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_get_bookings_by_flight(client, admin_headers, setup_flight_and_passenger):
    flight_id, passenger_id = setup_flight_and_passenger

    booking_data = {"flightId": flight_id, "passengerId": passenger_id}
    client.post("/bookings/", json=booking_data, headers=admin_headers)

    response = client.get(f"/bookings/by-flight/{flight_id}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["flightId"] == flight_id


def test_get_bookings_by_passenger(client, admin_headers, setup_flight_and_passenger, sample_passenger_data):
    flight_id, passenger_id = setup_flight_and_passenger

    booking_data = {"flightId": flight_id, "passengerId": passenger_id}
    client.post("/bookings/", json=booking_data, headers=admin_headers)

    passport = sample_passenger_data["passportNumber"]
    response = client.get(f"/bookings/by-passenger/{passport}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["passengerId"] == passenger_id


def test_get_all_bookings_paginated(client, admin_headers):
    response = client.get("/bookings", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


# Права доступа:
def test_sell_ticket_forbidden_for_guest(client, regular_user_headers, setup_flight_and_passenger):
    flight_id, passenger_id = setup_flight_and_passenger
    booking_data = {"flightId": flight_id, "passengerId": passenger_id}
    response = client.post("/bookings/", json=booking_data, headers=regular_user_headers)
    assert response.status_code == 403


def test_cancel_ticket_forbidden_for_dispatcher(client, regular_user_headers, setup_flight_and_passenger):
    # создаём "dispatcher"-пользователя
    dispatcher_token = register_and_login_user(client, "dispatch_test", "DispP@ss123!", role="dispatcher")
    dispatcher_headers = {"Authorization": f"Bearer {dispatcher_token}"}

    flight_id, passenger_id = setup_flight_and_passenger
    booking_data = {"flightId": flight_id, "passengerId": passenger_id}
    create_resp = client.post("/bookings/", json=booking_data, headers=dispatcher_headers)
    booking_id = create_resp.json()["id"]

    # dispatcher не может отменять (только admin)
    response = client.delete(f"/bookings/{booking_id}", headers=dispatcher_headers)
    assert response.status_code == 403