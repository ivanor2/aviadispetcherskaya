from sqlmodel import Session, select, delete
from fastapi import HTTPException, status

from app.models.airline import Airline
from app.models.booking import Booking
from app.models.flight import Flight
from app.models.airport import Airport
from app.models.passenger import Passenger
from app.schemas.flight_schema import FlightCreate, FlightUpdate
from typing import List, Optional


def create_flight(data: FlightCreate, session: Session) -> Flight:
    """
    Создание нового авиарейса с полной валидацией.
    При создании рейса free_seats автоматически устанавливается равным total_seats.
    """
    airline = session.exec(
        select(Airline).where(Airline.code == data.airlineCode.upper())
    ).first()
    if not airline:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Авиакомпания с кодом {data.airlineCode} не зарегистрирована в системе"
        )
    dep_airport = session.exec(
        select(Airport).where(Airport.icao_code == data.departureAirportIcao.upper())
    ).first()

    if not dep_airport:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Аэропорт отправления с ICAO-кодом {data.departureAirportIcao} не найден"
        )
    arr_airport = session.exec(
        select(Airport).where(Airport.icao_code == data.arrivalAirportIcao.upper())
    ).first()

    if not arr_airport:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Аэропорт прибытия с ICAO-кодом {data.arrivalAirportIcao} не найден"
        )
    if dep_airport.icao_code == arr_airport.icao_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Аэропорты отправления и прибытия не могут совпадать"
        )
    flight_prefix = data.flightNumber.split('-')[0].upper()
    if flight_prefix != data.airlineCode.upper():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Префикс номера рейса ({flight_prefix}) должен совпадать с кодом авиакомпании ({data.airlineCode})"
        )
    existing_flight = session.exec(
        select(Flight).where(Flight.flight_number == data.flightNumber.upper())
    ).first()
    if existing_flight:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Рейс с таким номером уже существует"
        )
    # ✅ free_seats всегда равно total_seats при создании рейса
    flight = Flight(
        flight_number=data.flightNumber.upper(),
        airline_code=data.airlineCode.upper(),
        departure_airport_icao=dep_airport.icao_code,
        arrival_airport_icao=arr_airport.icao_code,
        departure_date=data.departureDate,
        departure_time=data.departureTime,
        arrival_time=data.arrivalTime,
        total_seats=data.totalSeats,
        free_seats=data.totalSeats  # ✅ Игнорируем переданное значение, всегда ставим максимум
    )

    session.add(flight)
    session.commit()
    session.refresh(flight)

    return flight


def get_all_flights(session: Session) -> List[Flight]:
    return session.exec(select(Flight)).all()


def get_flight_by_id(flight_id: int, session: Session) -> Flight:
    flight = session.get(Flight, flight_id)
    if not flight:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рейс не найден")
    return flight


def get_flight_by_number(flight_number: str, session: Session) -> Flight:
    flight = session.exec(select(Flight).where(Flight.flight_number == flight_number.upper())).first()
    if not flight:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рейс не найден")
    return flight


def update_flight(flight_id: int, data: FlightUpdate, session: Session) -> Flight:
    flight = session.get(Flight, flight_id)
    if not flight:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рейс не найден")

    update_data = data.model_dump(exclude_unset=True)

    # Преобразуем camelCase -> snake_case
    snake_case_update_data = {}
    for key, value in update_data.items():
        snake_key = ''.join(['_' + c.lower() if c.isupper() else c for c in key]).lstrip('_')
        # Нормализуем ICAO-коды и номера рейсов
        if snake_key in ('departure_airport_icao', 'arrival_airport_icao', 'flight_number'):
            snake_case_update_data[snake_key] = value.upper()
        else:
            snake_case_update_data[snake_key] = value

    #  Валидация новых аэропортов при изменении
    if 'departure_airport_icao' in snake_case_update_data:
        dep = session.exec(
            select(Airport).where(Airport.icao_code == snake_case_update_data['departure_airport_icao'])).first()
        if not dep: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail="Аэропорт отправления не найден")

    if 'arrival_airport_icao' in snake_case_update_data:
        arr = session.exec(
            select(Airport).where(Airport.icao_code == snake_case_update_data['arrival_airport_icao'])).first()
        if not arr: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Аэропорт прибытия не найден")

    for key, value in snake_case_update_data.items():
        setattr(flight, key, value)

    session.add(flight)
    session.commit()
    session.refresh(flight)
    return flight


def delete_flight(flight_id: int, session: Session):
    """Удаление рейса с каскадным удалением связанных бронирований"""
    flight = session.get(Flight, flight_id)
    if not flight:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рейс не найден")

    # 1️⃣ Сначала удаляем все бронирования, привязанные к этому рейсу
    bookings_to_delete = session.exec(
        select(Booking).where(Booking.flight_id == flight_id)
    ).all()

    for booking in bookings_to_delete:
        session.delete(booking)

    # 2️⃣ Только теперь удаляем сам рейс
    session.delete(flight)
    session.commit()


def search_flights_by_arrival(airport_query: str, session: Session) -> List[Flight]:
    matching_airports = session.exec(
        select(Airport.icao_code).where(
            (Airport.name.contains(airport_query)) |
            (Airport.icao_code.contains(airport_query.upper()))
        )
    ).all()
    if not matching_airports:
        return []
    return session.exec(select(Flight).where(Flight.arrival_airport_icao.in_(matching_airports))).all()


def get_flight_with_passengers_by_number(flight_number: str, session: Session):
    flight = session.exec(select(Flight).where(Flight.flight_number == flight_number.upper())).first()
    if not flight:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рейс не найден")

    bookings = session.exec(select(Booking).where(Booking.flight_id == flight.id)).all()
    result = []
    for b in bookings:
        p = session.get(Passenger, b.passenger_id)
        result.append({
            "id": b.id,
            "booking_code": b.booking_code,
            "booked_at": b.created_at.isoformat() if b.created_at else None,
            "passenger": {
                "full_name": p.full_name if p else "Пассажир удалён",
                "passport_number": p.passport_number if p else "N/A"
            }
        })
    return flight, result


def delete_all_flights(session: Session):
    flight_ids = session.exec(select(Flight.id)).all()
    if flight_ids:
        session.exec(delete(Booking).where(Booking.flight_id.in_(flight_ids)))
    session.exec(delete(Flight))
    session.commit()