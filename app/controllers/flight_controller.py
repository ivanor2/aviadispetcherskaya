# app/controllers/flight_controller.py

from sqlmodel import Session, select
from fastapi import HTTPException, status
from app.models.flight import Flight
from app.models.airport import Airport # <-- Добавлен импорт
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
        # --- ИЗМЕНЕНО: Сохраняем id аэропортов ---
        departure_airport_id=data.departureAirportId,
        arrival_airport_id=data.arrivalAirportId,
        # --- /ИЗМЕНЕНО ---
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
    if 'departureAirportId' in update_data:
        dep_airport = session.get(Airport, update_data['departureAirportId'])
        if not dep_airport:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Аэропорт отправления с id {update_data['departureAirportId']} не найден"
            )
    if 'arrivalAirportId' in update_data:
        arr_airport = session.get(Airport, update_data['arrivalAirportId'])
        if not arr_airport:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Аэропорт прибытия с id {update_data['arrivalAirportId']} не найден"
            )
    # --- /ИЗМЕНЕНО ---

    for key, value in update_data.items():
        # Преобразование camelCase в snake_case
        snake_key = ''.join(['_' + c.lower() if c.isupper() else c for c in key]).lstrip('_')
        setattr(flight, snake_key, value)

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
