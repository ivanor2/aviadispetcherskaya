from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session, select, col, delete
from app.db.session import get_session
from app.models.flight import Flight
from app.models.booking import Booking
from app.models.airport import Airport
from app.models.passenger import Passenger
from app.schemas.flight_schema import FlightCreate, FlightUpdate, FlightResponse, FlightWithPassengersResponse
from app.core.security import admin_required, dispatcher_or_higher, get_current_user
from fastapi_pagination import Page
from datetime import date
from typing import List

router = APIRouter()

@router.get("", response_model=Page[FlightResponse])
def list_flights(session: Session = Depends(get_session), _=Depends(get_current_user),
                 airline_code: str = Query(None), date_from: date = Query(None), date_to: date = Query(None),
                 sort_by: str = Query("departure_date"), order: str = Query("desc")):
    q = select(Flight)
    if airline_code: q = q.where(Flight.airline_code == airline_code.upper())
    if date_from: q = q.where(Flight.departure_date >= date_from)
    if date_to: q = q.where(Flight.departure_date <= date_to)
    order_col = getattr(Flight, sort_by, Flight.departure_date)
    return q.order_by(order_col.asc() if order == "asc" else order_col.desc())

@router.get("/{flight_id}", response_model=FlightResponse)
def get_flight(flight_id: int, session: Session = Depends(get_session), _=Depends(get_current_user)):
    f = session.get(Flight, flight_id)
    if not f: raise status.HTTP_404_NOT_FOUND
    return f

@router.get("/search/by-arrival/{query}", response_model=List[FlightResponse])
def search_by_arrival(query: str, session: Session = Depends(get_session), _=Depends(get_current_user)):
    airport_icaos = session.exec(
        select(Airport.icao_code).where(
            col(Airport.name).ilike(f"%{query}%") | col(Airport.icao_code).ilike(f"%{query.upper()}%")
        )
    ).all()
    if not airport_icaos: return []
    return session.exec(select(Flight).where(Flight.arrival_airport_icao.in_(airport_icaos))).all()

@router.get("/by-number/{flight_number}", response_model=FlightWithPassengersResponse)
def get_by_number(flight_number: str, session: Session = Depends(get_session), _=Depends(dispatcher_or_higher)):
    f = session.exec(select(Flight).where(Flight.flight_number == flight_number.upper())).first()
    if not f: raise status.HTTP_404_NOT_FOUND
    bookings = session.exec(select(Booking).where(Booking.flight_id == f.id)).all()
    passengers_list = []
    for b in bookings:
        p = session.get(Passenger, b.passenger_id)
        passengers_list.append({
            "id": b.id, "booking_code": b.booking_code, "booked_at": b.created_at,
            "passenger": {"full_name": p.full_name if p else "Удалён", "passport_number": p.passport_number if p else "N/A"}
        })
    return {"flight": f, "passengers": passengers_list}

@router.post("", response_model=FlightResponse, status_code=201, dependencies=[Depends(dispatcher_or_higher)])
def create_flight(data: FlightCreate, session: Session = Depends(get_session)):
    f = Flight(**data.model_dump())
    session.add(f); session.commit(); session.refresh(f)
    return f

@router.put("/{flight_id}", response_model=FlightResponse, dependencies=[Depends(admin_required)])
def update_flight(flight_id: int, data: FlightUpdate, session: Session = Depends(get_session)):
    f = session.get(Flight, flight_id)
    if not f: raise status.HTTP_404_NOT_FOUND
    for k, v in data.model_dump(exclude_unset=True).items(): setattr(f, k, v)
    session.commit(); session.refresh(f)
    return f

@router.delete("/{flight_id}", status_code=204, dependencies=[Depends(admin_required)])
def delete_flight(flight_id: int, session: Session = Depends(get_session)):
    f = session.get(Flight, flight_id)
    if not f: raise status.HTTP_404_NOT_FOUND
    session.delete(f); session.commit()

@router.delete("/", status_code=204, dependencies=[Depends(admin_required)])
def delete_all(confirm: bool = Query(False), session: Session = Depends(get_session)):
    if not confirm: raise status.HTTP_400_BAD_REQUEST
    session.exec(delete(Booking))
    session.exec(delete(Flight))
    session.commit()