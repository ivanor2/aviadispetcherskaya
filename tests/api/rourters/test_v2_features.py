"""Тесты расширенных функций API v2.

Проверяют продвинутые возможности версии 2 API: поиск, сортировка,
бронирование и отмена билетов.
"""
# tests/api/rourters/test_v2_features.py
import pytest
from fastapi import status


@pytest.mark.usefixtures("db_session")
class TestV2AdvancedFeatures:
    """Набор тестов для проверки расширенных функций API v2."""

    def test_airport_search_and_sort(self, client, admin_token):
        """Тестирует поиск и сортировку аэропортов в API v2.
        
        Проверяет:
        - Создание двух аэропортов с валидными ICAO-кодами
        - Сортировку по имени в возрастающем порядке
        - Корректную структуру ответа с items
        """
        headers = {"Authorization": f"Bearer {admin_token}"}
        # ✅ Используем только валидные ICAO-коды из VALID_ICAO_PREFIXES
        ap1 = {"icaoCode": "AGEE", "name": "Sheremetyevo Intl"}
        ap2 = {"icaoCode": "AGDD", "name": "Vnukovo Intl"}

        r1 = client.post("/api/v2/airports", json=ap1, headers=headers)
        assert r1.status_code == 201, f"Создание 1: {r1.text}"
        r2 = client.post("/api/v2/airports", json=ap2, headers=headers)
        assert r2.status_code == 201, f"Создание 2: {r2.text}"

        res = client.get("/api/v2/airports?sort_by=name&order=asc", headers=headers)
        data = res.json()
        assert res.status_code == 200
        assert len(data["items"]) >= 2
        # Проверка сортировки по имени (Sheremetyevo < Vnukovo)
        assert data["items"][0]["name"] == "Sheremetyevo Intl"

    def test_booking_sell_and_list(self, client, admin_token, fake_passenger_data):
        """Тестирует продажу и отмену бронирования через API v2.
        
        Проверяет полный цикл:
        - Создание авиакомпании
        - Создание аэропортов вылета и прибытия
        - Создание рейса
        - Создание пассажира
        - Продажа билета (201)
        - Отмена бронирования (204)
        """
        headers = {"Authorization": f"Bearer {admin_token}"}

        # 1. Создаем авиакомпанию
        res_al = client.post("/api/v2/airlines", json={"code": "TST", "name": "Test Air"}, headers=headers)
        assert res_al.status_code == 201, f"Airline: {res_al.text}"

        # 2. Создаем аэропорты с ВАЛИДНЫМИ ICAO-кодами
        dep_icao = "AGDD"
        arr_icao = "AGEE"

        res_dep = client.post("/api/v2/airports", json={"icaoCode": dep_icao, "name": "Departure Test"},
                              headers=headers)
        assert res_dep.status_code == 201, f"Dep Airport: {res_dep.text}"

        res_arr = client.post("/api/v2/airports", json={"icaoCode": arr_icao, "name": "Arrival Test"}, headers=headers)
        assert res_arr.status_code == 201, f"Arr Airport: {res_arr.text}"

        # 3. Создаем рейс, ссылаясь на созданные ICAO-коды
        f_res = client.post("/api/v2/flights", json={
            "flightNumber": "TST-001",
            "airlineCode": "TST",
            "departureAirportIcao": dep_icao,
            "arrivalAirportIcao": arr_icao,
            "departureDate": "2026-12-12",
            "departureTime": "10:00:00",
            "totalSeats": 10,
            "freeSeats": 10
        }, headers=headers)
        assert f_res.status_code == 201, f"Flight: {f_res.text}"
        flight = f_res.json()

        # 4. Создаем пассажира
        p_res = client.post("/api/v2/passengers", json=fake_passenger_data, headers=headers)
        assert p_res.status_code == 201, f"Passenger: {p_res.text}"
        passenger = p_res.json()

        # 5. Оформляем бронирование
        res = client.post("/api/v2/bookings",
                          json={"flightId": flight["id"], "passengerIds": [passenger["id"]]},
                          headers=headers)
        assert res.status_code == 201, f"Booking: {res.text}"

        # 6. Отменяем бронирование (покрывает DELETE v2 и логику возврата мест)
        booking_id = res.json()[0]["id"]
        cancel_res = client.delete(f"/api/v2/bookings/{booking_id}", headers=headers)
        assert cancel_res.status_code == 204