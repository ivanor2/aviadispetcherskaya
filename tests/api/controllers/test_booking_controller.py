"""Тесты для контроллера бронирований.

Проверяют продажу и отмену билетов, работу с пересадками и обработку ошибок.
"""
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
    """Набор тестов для проверки функциональности booking_controller."""

    def setup_infra(self, db_session, fake_flight_data, fake_passenger_data):
        """Создает тестовые данные: рейс и пассажира.
        
        Args:
            db_session: Сессия базы данных.
            fake_flight_data: Данные для создания рейса.
            fake_passenger_data: Данные для создания пассажира.
            
        Returns:
            Кортеж (flight, passenger) - созданные объекты.
        """
        f = create_flight(FlightCreate(**fake_flight_data), db_session)
        p = create_passenger(PassengerCreate(**fake_passenger_data), db_session)
        return f, p

    def test_sell_success(self, db_session, fake_flight_data, fake_passenger_data):
        """Тестирует успешную продажу билета.
        
        Проверяет, что бронирование создается корректно.
        """
        f, p = self.setup_infra(db_session, fake_flight_data, fake_passenger_data)
        res = sell_ticket(BookingCreate(flightId=f.id, passengerIds=[p.id]), db_session)
        assert len(res) == 1
        # Проверяем, что место назначено
        assert res[0].seat is not None and res[0].seat != ""

    def test_sell_no_seats(self, db_session, fake_flight_data, fake_passenger_data):
        """Тестирует ошибку при продаже билета на рейс без мест.
        
        Проверяет, что попытка продажи при отсутствии мест вызывает HTTPException.
        create_flight всегда устанавливает free_seats = total_seats.
        generate_seat использует total_seats // 6 рядов, поэтому берём 6 мест (1 ряд),
        заполняем все 6 мест и потом пробуем продать ещё один билет.
        """
        from tests.conftest import fake as cfake
        fake_flight_data["totalSeats"] = 6
        f, p = self.setup_infra(db_session, fake_flight_data, fake_passenger_data)
        # Заполняем все 6 мест, создавая уникальных пассажиров
        passengers = [p]
        for i in range(5):
            extra = create_passenger(PassengerCreate(
                passportNumber=f"{cfake.numerify('7')}{i:03d}-{cfake.numerify('######')}",
                passportIssuedBy=f"City{i} UVMS",
                passportIssueDate="2021-01-01",
                fullName=f"Passenger {i}",
                birthDate="1988-01-01"
            ), db_session)
            passengers.append(extra)
        for px in passengers:
            sell_ticket(BookingCreate(flightId=f.id, passengerIds=[px.id]), db_session)
        
        # Теперь все места заняты, пробуем продать ещё один
        extra_p = create_passenger(PassengerCreate(
            passportNumber=f"9999-999999",
            passportIssuedBy="Last UVMS",
            passportIssueDate="2021-06-01",
            fullName="Last Passenger",
            birthDate="1985-05-15"
        ), db_session)
        with pytest.raises(HTTPException) as exc:
            sell_ticket(BookingCreate(flightId=f.id, passengerIds=[extra_p.id]), db_session)
        assert "Недостаточно мест" in exc.value.detail

    def test_sell_duplicate(self, db_session, fake_flight_data, fake_passenger_data):
        """Тестирует защиту от повторной продажи билета тому же пассажиру.
        
        Проверяет, что попытка продать билет повторно вызывает HTTPException.
        """
        f, p = self.setup_infra(db_session, fake_flight_data, fake_passenger_data)
        sell_ticket(BookingCreate(flightId=f.id, passengerIds=[p.id]), db_session)
        with pytest.raises(HTTPException) as exc:
            sell_ticket(BookingCreate(flightId=f.id, passengerIds=[p.id]), db_session)
        assert "уже куплен" in exc.value.detail.lower()

    def test_sell_with_custom_seats(self, db_session, fake_flight_data, fake_passenger_data):
        """Тестирует продажу билетов с указанием конкретных мест."""
        f, p = self.setup_infra(db_session, fake_flight_data, fake_passenger_data)
        res = sell_ticket(BookingCreate(flightId=f.id, passengerIds=[p.id], seats=["1A"]), db_session)
        assert len(res) == 1
        assert res[0].seat == "1A"

    def test_sell_seat_occupied(self, db_session, fake_flight_data, fake_passenger_data):
        """Тестирует ошибку при попытке занять уже занятое место."""
        from app.controllers.passenger_controller import create_passenger
        from app.schemas.passenger_schema import PassengerCreate
        from tests.conftest import fake as cfake
        
        f, p1 = self.setup_infra(db_session, fake_flight_data, fake_passenger_data)
        # Бронируем место 1A для первого пассажира
        sell_ticket(BookingCreate(flightId=f.id, passengerIds=[p1.id], seats=["1A"]), db_session)
        
        # Создаём второго пассажира с уникальным паспортом (иначе дубль паспорта)
        p2 = create_passenger(PassengerCreate(
            passportNumber=f"{cfake.numerify('8888')}-{cfake.numerify('888888')}",
            passportIssuedBy="Another UVMS",
            passportIssueDate="2022-03-10",
            fullName="Second Passenger",
            birthDate="1992-07-20"
        ), db_session)
        
        # Пытаемся забронировать то же место
        with pytest.raises(HTTPException) as exc:
            sell_ticket(BookingCreate(flightId=f.id, passengerIds=[p2.id], seats=["1A"]), db_session)
        assert "уже занято" in exc.value.detail.lower()

    def test_cancel_success(self, db_session, fake_flight_data, fake_passenger_data):
        """Тестирует успешную отмену бронирования.
        
        Проверяет, что после отмены количество мест восстанавливается.
        """
        f, p = self.setup_infra(db_session, fake_flight_data, fake_passenger_data)
        initial = f.free_seats
        b = sell_ticket(BookingCreate(flightId=f.id, passengerIds=[p.id]), db_session)[0]
        cancel_ticket(b.id, db_session)
        db_session.refresh(f)
        # После продажи и отмены количество мест должно вернуться к ИСХОДНОМУ, а не initial + 1
        assert f.free_seats == initial

    def test_get_by_flight(self, db_session, fake_flight_data, fake_passenger_data):
        """Тестирует получение списка бронирований по рейсу.
        
        Проверяет, что возвращается корректное количество бронирований.
        """
        f, p = self.setup_infra(db_session, fake_flight_data, fake_passenger_data)
        sell_ticket(BookingCreate(flightId=f.id, passengerIds=[p.id]), db_session)
        assert len(get_bookings_by_flight(f.id, db_session)) == 1

    def test_sell_ticket_with_connections(self, db_session, fake_flight_data, fake_passenger_data):
        """Тестирует продажу билета с пересадкой.
        
        Проверяет создание основного бронирования и бронирования пересадки.
        Покрывает строки 39-52 в booking_controller.py.
        """
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

        # Проверяем, что место списалось на рейсе пересадки (f2 создан с total_seats=150, free_seats=150, после продажи 1 билета должно стать 149)
        db_session.refresh(f2)
        assert f2.free_seats == 149

    def test_sell_ticket_flight_not_found(self, db_session, fake_passenger_data, max_flight_id):
        """Тестирует ошибку при продаже билета на несуществующий рейс.
        
        Проверяет, что запрос несуществующего рейса возвращает 404.
        Покрывает строку 24 в booking_controller.py.
        """
        from app.schemas.booking_schema import BookingCreate
        with pytest.raises(HTTPException) as exc:
            sell_ticket(BookingCreate(flightId=max_flight_id, passengerIds=[1]), db_session)
        assert exc.value.status_code == 404

    def test_add_connections_success(self, db_session, fake_flight_data, fake_passenger_data):
        """Тестирует добавление пересадки к существующему бронированию.
        
        Проверяет, что пересадка успешно добавляется к бронированию.
        Покрывает строки 79-115 в booking_controller.py.
        """
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