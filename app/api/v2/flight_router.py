from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlmodel import Session, select
from datetime import date
from app.db.session import get_session
from app.models.flight import Flight
from app.schemas.flight_schema import FlightCreate, FlightResponse
from app.core.security import admin_required, get_current_user
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate

router = APIRouter()


@router.get("", response_model=Page[FlightResponse])
def list_flights(session: Session = Depends(get_session), _=Depends(get_current_user)):
    return paginate(session, select(Flight).order_by(Flight.departure_date))


@router.post("", response_model=FlightResponse, status_code=status.HTTP_201_CREATED)
def create_flight(data: FlightCreate, session: Session = Depends(get_session), _=Depends(admin_required)):
    # Проверяем существование зависимостей
    from app.models.airline import Airline
    from app.models.airport import Airport
    from sqlmodel import select
    
    airline = session.exec(select(Airline).where(Airline.code == data.airlineCode.upper())).first()
    if not airline:
        raise HTTPException(status_code=400, detail="Авиакомпания не найдена")
    
    dep_airport = session.exec(select(Airport).where(Airport.icao_code == data.departureAirportIcao.upper())).first()
    if not dep_airport:
        raise HTTPException(status_code=400, detail="Аэропорт отправления не найден")
    
    arr_airport = session.exec(select(Airport).where(Airport.icao_code == data.arrivalAirportIcao.upper())).first()
    if not arr_airport:
        raise HTTPException(status_code=400, detail="Аэропорт прибытия не найден")
    
    if dep_airport.icao_code == arr_airport.icao_code:
        raise HTTPException(status_code=400, detail="Аэропорты отправления и прибытия не могут совпадать")
    
    flight = Flight(
        flight_number=data.flightNumber,
        airline_code=data.airlineCode,
        departure_airport_icao=data.departureAirportIcao,
        arrival_airport_icao=data.arrivalAirportIcao,
        departure_date=data.departureDate,
        departure_time=data.departureTime,
        arrival_time=data.arrivalTime,
        total_seats=data.totalSeats,
        free_seats=data.totalSeats  # ✅ Всегда устанавливаем максимальное количество
    )
    session.add(flight)
    session.commit()
    session.refresh(flight)
    return flight

@router.delete("/{flight_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flight(flight_id: int, session: Session = Depends(get_session), _=Depends(admin_required)):
    flight = session.get(Flight, flight_id)
    if not flight:
        raise HTTPException(status_code=404, detail="Рейс не найден")
    session.delete(flight)
    session.commit()