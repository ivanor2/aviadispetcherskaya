import pytest
from fastapi import HTTPException
from pydantic import ValidationError  # ✅ Добавлено для теста префикса
from sqlmodel import select
from app.models.flight import Flight  # ✅ Исправлен импорт
from app.controllers.flight_controller import (
    create_flight, get_flight_by_id, delete_flight,
    search_flights_by_arrival, delete_all_flights, update_flight, get_flight_with_passengers_by_number
)
from app.schemas.flight_schema import FlightCreate, FlightUpdate
from app.schemas.passenger_schema import PassengerCreate
from app.controllers.passenger_controller import create_passenger
from app.controllers.booking_controller import sell_ticket
from app.schemas.booking_schema import BookingCreate


@pytest.mark.usefixtures("db_session")
class TestFlightController:
    def test_create_success(self, db_session, fake_flight_data):
        f = create_flight(FlightCreate(**fake_flight_data), db_session)
        assert f.flight_number == fake_flight_data["flightNumber"]

    def test_create_airline_not_found(self, db_session, fake_flight_data):
        fake_flight_data["airlineCode"] = "XXX"
        fake_flight_data["flightNumber"] = "XXX-111"
        with pytest.raises(HTTPException) as exc:
            create_flight(FlightCreate(**fake_flight_data), db_session)
        assert "не зарегистрирована" in exc.value.detail

    def test_create_same_airports(self, db_session, fake_flight_data):
        fake_flight_data["arrivalAirportIcao"] = fake_flight_data["departureAirportIcao"]
        with pytest.raises(HTTPException) as exc:
            create_flight(FlightCreate(**fake_flight_data), db_session)
        assert "не могут совпадать" in exc.value.detail

    def test_create_prefix_mismatch(self, db_session, fake_flight_data):
        fake_flight_data["flightNumber"] = "MIS-111"  # Префикс MIS != airlineCode
        # ✅ ИСПРАВЛЕНО: Ожидаем ValidationError от Pydantic, а не HTTPException
        with pytest.raises(ValidationError):
            create_flight(FlightCreate(**fake_flight_data), db_session)

    def test_get_by_id_success(self, db_session, fake_flight_data):
        f = create_flight(FlightCreate(**fake_flight_data), db_session)
        assert get_flight_by_id(f.id, db_session).id == f.id

    def test_get_by_id_not_found(self, db_session, max_flight_id):
        with pytest.raises(HTTPException) as exc:
            get_flight_by_id(max_flight_id, db_session)
        assert exc.value.status_code == 404

    def test_update_success(self, db_session, fake_flight_data):
        f = create_flight(FlightCreate(**fake_flight_data), db_session)
        upd = update_flight(f.id, FlightUpdate(totalSeats=200), db_session)
        assert upd.total_seats == 200

    def test_delete_cascade(self, db_session, fake_flight_data, fake_passenger_data):
        f = create_flight(FlightCreate(**fake_flight_data), db_session)
        p = create_passenger(PassengerCreate(**fake_passenger_data), db_session)
        sell_ticket(BookingCreate(flightId=f.id, passengerIds=[p.id]), db_session)

        delete_flight(f.id, db_session)
        with pytest.raises(HTTPException):
            get_flight_by_id(f.id, db_session)

    def test_search_by_arrival_found(self, db_session, fake_flight_data):
        create_flight(FlightCreate(**fake_flight_data), db_session)
        res = search_flights_by_arrival("Arrival",
                                        db_session)  # Ищем по имени, которое было сгенерировано как "Arrival"
        assert len(res) >= 1

    def test_delete_all(self, db_session, fake_flight_data):
        create_flight(FlightCreate(**fake_flight_data), db_session)
        delete_all_flights(db_session)
        # ✅ ИСПРАВЛЕНО: f.__class__ заменено на Flight
        assert db_session.exec(select(Flight)).all() == []

    def test_search_flights_empty(self, db_session):
        """Тестирует поиск при отсутствии результатов (покрывает строки 143-145)"""
        res = search_flights_by_arrival("NONEXISTENT", db_session)
        assert res == []

    def test_get_flight_with_passengers_success(self, db_session, fake_flight_data, fake_passenger_data):
        """Тестирует получение рейса с пассажирами (покрывает строки 148-163)"""
        from app.schemas.flight_schema import FlightCreate
        from app.schemas.passenger_schema import PassengerCreate
        from app.schemas.booking_schema import BookingCreate
        from app.controllers.booking_controller import sell_ticket

        f = create_flight(FlightCreate(**fake_flight_data), db_session)
        p = create_passenger(PassengerCreate(**fake_passenger_data), db_session)
        sell_ticket(BookingCreate(flightId=f.id, passengerIds=[p.id]), db_session)

        flight, passengers = get_flight_with_passengers_by_number(fake_flight_data["flightNumber"], db_session)
        assert flight.id == f.id
        assert len(passengers) == 1