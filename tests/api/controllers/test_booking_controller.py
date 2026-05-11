import pytest
from fastapi import HTTPException
from app.controllers.booking_controller import sell_ticket, cancel_ticket, get_bookings_by_flight, get_bookings_by_passenger
from app.schemas.booking_schema import BookingCreate
from app.controllers.flight_controller import create_flight
from app.controllers.passenger_controller import create_passenger
from app.schemas.flight_schema import FlightCreate
from app.schemas.passenger_schema import PassengerCreate
from tests.conftest import fake

@pytest.mark.usefixtures("db_session")
class TestBookingController:
    def setup_infra(self, db_session, fake_flight_data, fake_passenger_data):
        f = create_flight(FlightCreate(**fake_flight_data), db_session)
        p = create_passenger(PassengerCreate(**fake_passenger_data), db_session)
        return f, p

    def test_sell_success(self, db_session, fake_flight_data, fake_passenger_data):
        f, p = self.setup_infra(db_session, fake_flight_data, fake_passenger_data)
        res = sell_ticket(BookingCreate(flightId=f.id, passengerIds=[p.id]), db_session)
        assert len(res) == 1

    def test_sell_no_seats(self, db_session, fake_flight_data, fake_passenger_data):
        fake_flight_data["freeSeats"] = 0
        f, p = self.setup_infra(db_session, fake_flight_data, fake_passenger_data)
        with pytest.raises(HTTPException) as exc:
            sell_ticket(BookingCreate(flightId=f.id, passengerIds=[p.id]), db_session)
        assert "Недостаточно мест" in exc.value.detail

    def test_sell_duplicate(self, db_session, fake_flight_data, fake_passenger_data):
        f, p = self.setup_infra(db_session, fake_flight_data, fake_passenger_data)
        sell_ticket(BookingCreate(flightId=f.id, passengerIds=[p.id]), db_session)
        with pytest.raises(HTTPException) as exc:
            sell_ticket(BookingCreate(flightId=f.id, passengerIds=[p.id]), db_session)
        assert "уже куплен" in exc.value.detail.lower()

    def test_cancel_success(self, db_session, fake_flight_data, fake_passenger_data):
        f, p = self.setup_infra(db_session, fake_flight_data, fake_passenger_data)
        initial = f.free_seats
        b = sell_ticket(BookingCreate(flightId=f.id, passengerIds=[p.id]), db_session)[0]
        cancel_ticket(b.id, db_session)
        db_session.refresh(f)
        # После продажи и отмены количество мест должно вернуться к ИСХОДНОМУ, а не initial + 1
        assert f.free_seats == initial

    def test_get_by_flight(self, db_session, fake_flight_data, fake_passenger_data):
        f, p = self.setup_infra(db_session, fake_flight_data, fake_passenger_data)
        sell_ticket(BookingCreate(flightId=f.id, passengerIds=[p.id]), db_session)
        assert len(get_bookings_by_flight(f.id, db_session)) == 1

    def test_sell_ticket_with_connections(self, db_session, fake_flight_data, fake_passenger_data):
        """Тестирует продажу билета с пересадкой (покрывает строки 39-52)"""
        from app.schemas.flight_schema import FlightCreate
        from app.schemas.booking_schema import BookingCreate
        from app.controllers.flight_controller import create_flight
        from app.controllers.passenger_controller import create_passenger
        from app.controllers.booking_controller import sell_ticket

        # 1. Создаем основной рейс
        f1 = create_flight(FlightCreate(**fake_flight_data), db_session)

        # 2. Создаем рейс пересадки
        # Важно: flightNumber должен быть уникальным и соответствовать airlineCode
        f2_data = fake_flight_data.copy()
        f2_data["flightNumber"] = f"{fake_flight_data['airlineCode']}-999"

        # Создаем второй рейс
        f2 = create_flight(FlightCreate(**f2_data), db_session)

        # 3. Создаем пассажира
        p = create_passenger(PassengerCreate(**fake_passenger_data), db_session)

        # 4. Продаем билет с пересадкой
        # Передаем ID основного рейса и список ID рейсов пересадки
        bookings = sell_ticket(
            BookingCreate(flightId=f1.id, passengerIds=[p.id], connectionFlightIds=[f2.id]),
            db_session
        )

        # Проверяем, что создалось 2 бронирования (основное + пересадка)
        assert len(bookings) == 2

        # Проверяем, что место списалось на рейсе пересадки
        db_session.refresh(f2)
        assert f2.free_seats == 49

    def test_sell_ticket_flight_not_found(self, db_session, fake_passenger_data, max_flight_id):
        """Тестирует ошибку, если рейс не найден (покрывает строку 24)"""
        from app.schemas.booking_schema import BookingCreate
        with pytest.raises(HTTPException) as exc:
            sell_ticket(BookingCreate(flightId=max_flight_id, passengerIds=[1]), db_session)
        assert exc.value.status_code == 404

    def test_add_connections_success(self, db_session, fake_flight_data, fake_passenger_data):
        """Тестирует добавление пересадки к существующему бронированию (покрывает строки 79-115)"""
        from app.schemas.flight_schema import FlightCreate
        from app.schemas.booking_schema import BookingCreate
        from app.controllers.booking_controller import add_connections_to_booking

        f = create_flight(FlightCreate(**fake_flight_data), db_session)
        p = create_passenger(PassengerCreate(**fake_passenger_data), db_session)
        b = sell_ticket(BookingCreate(flightId=f.id, passengerIds=[p.id]), db_session)[0]

        # ✅ ИСПРАВЛЕНО: Валидный номер рейса пересадки
        f2_data = fake_flight_data.copy()
        f2_data["flightNumber"] = f"{fake_flight_data['airlineCode']}-888"
        f2 = create_flight(FlightCreate(**f2_data), db_session)

        res = add_connections_to_booking(b.booking_code, [f2.id], db_session)
        assert len(res) == 1