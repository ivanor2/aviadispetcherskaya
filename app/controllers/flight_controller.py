# app/controllers/flight_controller.py

from sqlmodel import Session, select, delete
from fastapi import HTTPException, status

from app.models.booking import Booking
from app.models.flight import Flight
from app.models.airport import Airport # <-- Добавлен импорт
from app.models.passenger import Passenger
from app.schemas.flight_schema import FlightCreate, FlightUpdate
from typing import List, Optional

def create_flight(data: FlightCreate, session: Session) -> Flight:
    """Создание рейса"""
    # --- ИЗМЕНЕНО: Проверка существования аэропортов по id ---
    departure_airport = session.get(Airport, data.departureAirportId)
    if not departure_airport:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Аэропорт отправления с id {data.departureAirportId} не найден"
        )

    arrival_airport = session.get(Airport, data.arrivalAirportId)
    if not arrival_airport:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Аэропорт прибытия с id {data.arrivalAirportId} не найден"
        )
    # --- /ИЗМЕНЕНО ---

    existing = session.exec(
        select(Flight).where(Flight.flight_number == data.flightNumber)
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Рейс с таким номером уже существует"
        )

    flight = Flight(
        flight_number=data.flightNumber,
        airline_name=data.airlineName,
        departure_airport_id=data.departureAirportId,
        arrival_airport_id=data.arrivalAirportId,
        departure_date=data.departureDate,
        departure_time=data.departureTime,
        total_seats=data.totalSeats,
        free_seats=data.freeSeats
    )
    session.add(flight)
    session.commit()
    session.refresh(flight)
    return flight

def get_all_flights(session: Session) -> List[Flight]:
    """Получение всех рейсов"""
    return session.exec(select(Flight)).all()

def get_flight_by_id(flight_id: int, session: Session) -> Flight:
    """Получение рейса по ID"""
    flight = session.get(Flight, flight_id)
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Рейс не найден"
        )
    return flight

def get_flight_by_number(flight_number: str, session: Session) -> Optional[Flight]:
    """Получение рейса по номеру"""
    flight = session.exec(
        select(Flight).where(Flight.flight_number == flight_number)
    ).first()

    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Рейс не найден"
        )
    return flight

def update_flight(flight_id: int, data: FlightUpdate, session: Session) -> Flight:
    """Обновление рейса"""
    flight = session.get(Flight, flight_id)
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Рейс не найден"
        )

    # --- ИЗМЕНЕНО: Проверка существования новых аэропортов по id, если они меняются ---
    update_data = data.model_dump(exclude_unset=True)

    # Преобразуем camelCase в snake_case для всех полей, включая ID аэропортов
    snake_case_update_data = {}
    for key, value in update_data.items():
        snake_key = ''.join(['_' + c.lower() if c.isupper() else c for c in key]).lstrip('_')
        snake_case_update_data[snake_key] = value

    # Проверяем, меняются ли ID аэропортов
    if 'departure_airport_id' in snake_case_update_data:
        dep_airport_id = snake_case_update_data['departure_airport_id']
        dep_airport = session.get(Airport, dep_airport_id)
        if not dep_airport:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Аэропорт отправления с id {dep_airport_id} не найден"
            )
    if 'arrival_airport_id' in snake_case_update_data:
        arr_airport_id = snake_case_update_data['arrival_airport_id']
        arr_airport = session.get(Airport, arr_airport_id)
        if not arr_airport:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Аэропорт прибытия с id {arr_airport_id} не найден"
            )

    # Применяем обновленные данные
    for key, value in snake_case_update_data.items():
        setattr(flight, key, value)

    session.add(flight)
    session.commit()
    session.refresh(flight)
    return flight

def delete_flight(flight_id: int, session: Session):
    """Удаление рейса"""
    flight = session.get(Flight, flight_id)
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Рейс не найден"
        )

    session.delete(flight)
    session.commit()

def search_flights_by_arrival(airport_query: str, session: Session) -> List[Flight]:
    """Поиск рейсов по аэропорту прибытия (теперь по id)"""
    # Сначала ищем аэропорты, чьё имя или ICAO содержат запрос
    # Это позволяет искать по названию, как было раньше, но возвращать id
    matching_airports = session.exec(
        select(Airport.id).where(
            (Airport.name.contains(airport_query)) |
            (Airport.icao_code.contains(airport_query.upper()))
        )
    ).all()

    if not matching_airports:
        return [] # Нет аэропортов, соответствующих запросу

    # Затем ищем рейсы, прибывающие в эти аэропорты
    flights = session.exec(
        select(Flight).where(Flight.arrival_airport_id.in_(matching_airports))
    ).all()
    return flights

# app/controllers/flight_controller.py

# (в конце файла, после search_flights_by_arrival)

def get_flight_with_passengers_by_number(flight_number: str, session: Session):
    """
    Получение рейса по номеру с полной информацией о пассажирах.
    """
    flight = session.exec(
        select(Flight).where(Flight.flight_number == flight_number)
    ).first()

    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Рейс не найден"
        )

    # Получаем все бронирования для этого рейса
    bookings = session.exec(
        select(Booking).where(Booking.flight_id == flight.id)
    ).all()

    # Получаем пассажиров по их ID из бронирований
    passenger_ids = [b.passenger_id for b in bookings]
    passengers = []
    if passenger_ids:
        passengers = session.exec(
            select(Passenger).where(Passenger.id.in_(passenger_ids))
        ).all()

    return flight, passengers

# app/controllers/flight_controller.py

# app/controllers/flight_controller.py

def delete_all_flights(session: Session):
    """
    Удаляет все авиарейсы и связанные с ними бронирования.
    """

    flight_ids_result = session.exec(select(Flight.id))
    flight_ids = flight_ids_result.all()

    if flight_ids:
        session.exec(delete(Booking).where(Booking.flight_id.in_(flight_ids)))

    session.exec(delete(Flight))

    session.commit()