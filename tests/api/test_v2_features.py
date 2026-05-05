# tests/api/test_v2_features.py
import pytest
from fastapi import status


def test_v2_airport_search(client, admin_token):
    """Тест поиска аэропортов в v2"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Создаём тестовые аэропорты
    airports = [
        {"icaoCode": "SVO1", "name": "Sheremetyevo Test"},
        {"icaoCode": "DME1", "name": "Domodedovo Test"},
        {"icaoCode": "VKO1", "name": "Vnukovo Test"},
    ]
    for ap in airports:
        client.post("/api/v2/airports", json=ap, headers=headers)

    # Поиск по названию
    response = client.get("/api/v2/airports?search=Sher", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert any("Sheremetyevo" in item.get("name", "") for item in data["items"])

    # Поиск по ICAO
    response = client.get("/api/v2/airports?search=DME", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert any(item.get("icaoCode") == "DME1" for item in data["items"])


def test_v2_airport_sorting(client, admin_token):
    """Тест сортировки аэропортов в v2"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Создаём аэропорты в случайном порядке
    airports = [
        {"icaoCode": "ZZZZ", "name": "Zulu Airport"},
        {"icaoCode": "AAAA", "name": "Alpha Airport"},
        {"icaoCode": "MMMM", "name": "Mike Airport"},
    ]
    for ap in airports:
        client.post("/api/v2/airports", json=ap, headers=headers)

    # Сортировка по названию по возрастанию
    response = client.get("/api/v2/airports?sort_by=name&order=asc", headers=headers)
    assert response.status_code == 200
    names = [item["name"] for item in response.json()["items"]]
    assert names == sorted(names)

    # Сортировка по убыванию
    response = client.get("/api/v2/airports?sort_by=name&order=desc", headers=headers)
    assert response.status_code == 200
    names = [item["name"] for item in response.json()["items"]]
    assert names == sorted(names, reverse=True)


def test_v2_flight_filtering(client, admin_token):
    """Тест фильтрации рейсов в v2"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    from datetime import date
    # Создаём рейсы разных авиакомпаний
    from app.controllers import airline_controller, airport_controller, flight_controller
    from app.schemas import AirlineCreate, AirportCreate, FlightCreate
    from sqlmodel import Session
    from app.db.database import engine

    with Session(engine) as session:
        airline_controller.create_airline(AirlineCreate(code="AAA", name="AAA Air"), session)
        airline_controller.create_airline(AirlineCreate(code="BBB", name="BBB Air"), session)
        airport_controller.create_airport(AirportCreate(icaoCode="F1", name="F1"), session)
        airport_controller.create_airport(AirportCreate(icaoCode="F2", name="F2"), session)

        flight_controller.create_flight(FlightCreate(
            flightNumber="AAA-100", airlineCode="AAA",
            departureAirportIcao="F1", arrivalAirportIcao="F2",
            departureDate=date(2026, 12, 1), departureTime="10:00:00",
            totalSeats=100, freeSeats=50
        ), session)

        flight_controller.create_flight(FlightCreate(
            flightNumber="BBB-200", airlineCode="BBB",
            departureAirportIcao="F1", arrivalAirportIcao="F2",
            departureDate=date(2026, 12, 2), departureTime="11:00:00",
            totalSeats=100, freeSeats=50
        ), session)

    # Фильтрация по авиакомпании
    response = client.get("/api/v2/flights?airline_code=AAA", headers=headers)
    assert response.status_code == 200
    items = response.json()["items"]
    assert all(item["airlineCode"] == "AAA" for item in items)

    # Фильтрация по дате
    response = client.get("/api/v2/flights?date_from=2026-12-02", headers=headers)
    assert response.status_code == 200
    items = response.json()["items"]
    assert all(item["departureDate"] >= "2026-12-02" for item in items)


def test_v2_passenger_search_by_name(client, admin_token):
    """Тест поиска пассажиров по имени в v2"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    passengers = [
        {"passportNumber": "1000-000001", "passportIssuedBy": "Test",
         "passportIssueDate": "2020-01-01", "fullName": "Иванов Иван", "birthDate": "1990-01-01"},
        {"passportNumber": "1000-000002", "passportIssuedBy": "Test",
         "passportIssueDate": "2020-01-01", "fullName": "Петров Пётр", "birthDate": "1991-01-01"},
        {"passportNumber": "1000-000003", "passportIssuedBy": "Test",
         "passportIssueDate": "2020-01-01", "fullName": "Иванов Сергей", "birthDate": "1992-01-01"},
    ]
    for p in passengers:
        client.post("/api/v2/passengers", json=p, headers=headers)


    response = client.get("/api/v2/passengers?search=Иванов", headers=headers)
    assert response.status_code == 200
    items = response.json()["items"]
    assert all("Иванов" in item["fullName"] for item in items)
    assert len(items) == 2


def test_v2_booking_filtering(client, admin_token):
    """Тест фильтрации бронирований в v2"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/api/v2/bookings?flight_id=1", headers=headers)
    assert response.status_code == 200
