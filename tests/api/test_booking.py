import pytest
from fastapi import status

def test_sell_ticket_workflow(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    # 1. Создаем аэропорты, авиакомпанию, рейс, пассажира (упрощенно)
    client.post("/api/v2/airports", json={"icaoCode": "DEP1", "name": "Dep"}, headers=headers)
    client.post("/api/v2/airports", json={"icaoCode": "ARR1", "name": "Arr"}, headers=headers)
    client.post("/api/v2/airlines", json={"code": "TST", "name": "TestAir"}, headers=headers)
    flight = client.post("/api/v2/flights", json={
        "flightNumber": "TST-101", "airlineCode": "TST",
        "departureAirportIcao": "DEP1", "arrivalAirportIcao": "ARR1",
        "departureDate": "2026-12-01", "departureTime": "10:00:00",
        "totalSeats": 50, "freeSeats": 50
    }, headers=headers).json()
    p = client.post("/api/v2/passengers", json={
        "passportNumber": "1234-567890", "passportIssuedBy": "MVD",
        "passportIssueDate": "2020-01-01", "fullName": "Ivanov I.", "birthDate": "1990-01-01"
    }, headers=headers).json()

    # 2. Продажа билета
    booking = client.post("/api/v2/bookings", json={
        "flightId": flight["id"], "passengerIds": [p["id"]]
    }, headers=headers)
    assert booking.status_code == 201
    assert booking.json()[0]["bookingCode"] is not None

    # 3. Дубликат билета
    dup = client.post("/api/v2/bookings", json={
        "flightId": flight["id"], "passengerIds": [p["id"]]
    }, headers=headers)
    assert dup.status_code == 400