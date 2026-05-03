from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.booking import Booking, generate_booking_code
from app.models.flight import Flight
from app.models.passenger import Passenger
from app.schemas.booking_schema import BookingCreate, BookingResponse, ConnectionAddPayload
from app.core.security import admin_required, dispatcher_or_higher, get_current_user
from fastapi_pagination import Page
from typing import List

router = APIRouter()

@router.get("", response_model=Page[BookingResponse])
def list_bookings(session: Session = Depends(get_session), _=Depends(dispatcher_or_higher),
                  flight_id: int = Query(None), passenger_id: int = Query(None),
                  sort_by: str = Query("created_at"), order: str = Query("desc")):
    q = select(Booking)
    if flight_id: q = q.where(Booking.flight_id == flight_id)
    if passenger_id: q = q.where(Booking.passenger_id == passenger_id)
    order_col = getattr(Booking, sort_by, Booking.created_at)
    return q.order_by(order_col.asc() if order == "asc" else order_col.desc())

@router.post("/", response_model=List[BookingResponse], status_code=201, dependencies=[Depends(dispatcher_or_higher)])
def create_booking(data: BookingCreate, session: Session = Depends(get_session)):
    p_count = len(data.passengerIds)
    flight = session.get(Flight, data.flightId)
    if not flight or flight.free_seats < p_count: raise status.HTTP_400_BAD_REQUEST
    passengers = session.exec(select(Passenger).where(Passenger.id.in_(data.passengerIds))).all()
    if len(passengers) != p_count: raise status.HTTP_400_BAD_REQUEST
    existing = session.exec(select(Booking).where(Booking.flight_id == data.flightId, Booking.passenger_id.in_(data.passengerIds))).all()
    if existing: raise status.HTTP_400_BAD_REQUEST

    booking_code = data.bookingCode or generate_booking_code()
    created = []
    for p_id in data.passengerIds:
        b = Booking(booking_code=booking_code, flight_id=data.flightId, passenger_id=p_id)
        session.add(b); created.append(b)
    flight.free_seats -= p_count; session.add(flight)
    session.commit()
    return created

@router.post("/{booking_code}/connections", response_model=List[BookingResponse], status_code=201)
def add_connections(booking_code: str, payload: ConnectionAddPayload, session: Session = Depends(get_session), _=Depends(dispatcher_or_higher)):
    existing = session.exec(select(Booking).where(Booking.booking_code == booking_code)).all()
    if not existing: raise status.HTTP_404_NOT_FOUND
    p_ids = list(set(b.passenger_id for b in existing))
    p_count = len(p_ids)
    created = []
    for fid in payload.flightIds:
        cf = session.get(Flight, fid)
        if not cf or cf.free_seats < p_count: raise status.HTTP_400_BAD_REQUEST
        for p_id in p_ids:
            b = Booking(booking_code=booking_code, flight_id=fid, passenger_id=p_id)
            session.add(b); created.append(b)
        cf.free_seats -= p_count; session.add(cf)
    session.commit()
    return created

@router.delete("/{booking_id}", status_code=204, dependencies=[Depends(admin_required)])
def cancel_booking(booking_id: int, session: Session = Depends(get_session)):
    b = session.get(Booking, booking_id)
    if not b: raise status.HTTP_404_NOT_FOUND
    f = session.get(Flight, b.flight_id)
    if f: f.free_seats += 1; session.add(f)
    session.delete(b); session.commit()

@router.get("/by-flight/{flight_id}", response_model=List[BookingResponse])
def get_by_flight(flight_id: int, session: Session = Depends(get_session), _=Depends(get_current_user)):
    return session.exec(select(Booking).where(Booking.flight_id == flight_id)).all()

@router.get("/by-passenger/{passport}", response_model=List[BookingResponse])
def get_by_passenger(passport: str, session: Session = Depends(get_session), _=Depends(get_current_user)):
    p = session.exec(select(Passenger).where(Passenger.passport_number == passport)).first()
    if not p: return []
    return session.exec(select(Booking).where(Booking.passenger_id == p.id)).all()