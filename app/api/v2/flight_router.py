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
    flight = Flight(
        flight_number=data.flightNumber,
        airline_code=data.airlineCode,
        departure_airport_icao=data.departureAirportIcao,
        arrival_airport_icao=data.arrivalAirportIcao,
        departure_date=data.departureDate,
        departure_time=data.departureTime,
        arrival_time=data.arrivalTime,
        total_seats=data.totalSeats,
        free_seats=data.freeSeats
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