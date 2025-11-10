from sqlmodel import Session, select
from fastapi import HTTPException, status
from app.models.flight import Flight
from app.schemas.flight_schema import FlightCreate, FlightUpdate
from typing import List, Optional


def create_flight(data: FlightCreate, session: Session) -> Flight:
    """Создание рейса"""
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
        departure_airport_icao=data.departureAirportIcao,
        arrival_airport_icao=data.arrivalAirportIcao,
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

    update_data = data.dict(exclude_unset=True)
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
    """Поиск рейсов по аэропорту прибытия"""
    flights = session.exec(
        select(Flight).where(Flight.arrival_airport_icao.contains(airport_query.upper()))
    ).all()
    return flights
