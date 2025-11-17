# app/api/v1/flight_router.py

from fastapi import APIRouter, Depends, status, Response
from sqlmodel import Session, select # Добавлен импорт select
from app.db.session import get_session
from app.schemas.flight_schema import FlightCreate, FlightUpdate, FlightResponse
from app.controllers.flight_controller import *
from app.core.security import get_current_user, admin_required
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate
from typing import List

# Удалены неправильные импорты, связанные с пассажирами
# from app.controllers.passenger_controller import create_passenger, ...
# from app.models.passenger import Passenger
# from app.schemas.passenger_schema import PassengerResponse, PassengerCreate

router = APIRouter(prefix="/flights", tags=["Авиарейсы"])

# --- CRUD для РЕЙСОВ ---
@router.post("", response_model=FlightResponse, status_code=status.HTTP_201_CREATED)
def create_flight_endpoint(
    data: FlightCreate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user) # Предполагается, что создание доступно аутентифицированным пользователям
):
    """Создание рейса"""
    flight = create_flight(data, session)
    return FlightResponse(
        id=flight.id,
        flightNumber=flight.flight_number,
        airlineName=flight.airline_name,
        departureAirportIcao=flight.departure_airport_icao,
        arrivalAirportIcao=flight.arrival_airport_icao,
        departureDate=flight.departure_date,
        departureTime=flight.departure_time,
        totalSeats=flight.total_seats,
        freeSeats=flight.free_seats
    )

@router.get("", response_model=Page[FlightResponse]) # Используем Page для пагинации
def get_flights_endpoint(session: Session = Depends(get_session)):
    """Просмотр всех рейсов с пагинацией"""
    return paginate(session, select(Flight))

@router.get("/{flight_id}", response_model=FlightResponse)
def get_flight_endpoint(flight_id: int, session: Session = Depends(get_session)):
    """Получение рейса по ID"""
    flight = get_flight_by_id(flight_id, session)
    return FlightResponse(
        id=flight.id,
        flightNumber=flight.flight_number,
        airlineName=flight.airline_name,
        departureAirportIcao=flight.departure_airport_icao,
        arrivalAirportIcao=flight.arrival_airport_icao,
        departureDate=flight.departure_date,
        departureTime=flight.departure_time,
        totalSeats=flight.total_seats,
        freeSeats=flight.free_seats
    )

@router.put("/{flight_id}", response_model=FlightResponse)
def update_flight_endpoint(
    flight_id: int,
    data: FlightUpdate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user) # Аутентификация требуется
):
    """Обновление рейса по ID"""
    flight = update_flight(flight_id, data, session)
    if not flight:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рейс не найден")
    return FlightResponse(
        id=flight.id,
        flightNumber=flight.flight_number,
        airlineName=flight.airline_name,
        departureAirportIcao=flight.departure_airport_icao,
        arrivalAirportIcao=flight.arrival_airport_icao,
        departureDate=flight.departure_date,
        departureTime=flight.departure_time,
        totalSeats=flight.total_seats,
        freeSeats=flight.free_seats
    )

@router.delete("/{flight_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flight_endpoint(
    flight_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(admin_required)
):
    """Удаление рейса по ID (только для администратора)"""
    delete_flight(flight_id, session)
    return # 204 No Content

# --- Поиск ---
@router.get("/search/by-arrival/{airport_query}", response_model=List[FlightResponse])
def search_flights_by_arrival_endpoint(airport_query: str, session: Session = Depends(get_session)):
    """Поиск рейсов по аэропорту прибытия (частичное совпадение)"""
    flights = search_flights_by_arrival(airport_query, session)
    return [
        FlightResponse(
            id=f.id,
            flightNumber=f.flight_number,
            airlineName=f.airline_name,
            departureAirportIcao=f.departure_airport_icao,
            arrivalAirportIcao=f.arrival_airport_icao,
            departureDate=f.departure_date,
            departureTime=f.departure_time,
            totalSeats=f.total_seats,
            freeSeats=f.free_seats
        )
        for f in flights
    ]
