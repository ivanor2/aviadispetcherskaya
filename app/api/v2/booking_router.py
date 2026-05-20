from typing import List

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.booking import Booking, generate_booking_code
from app.models.flight import Flight
from app.models.passenger import Passenger
from app.schemas.booking_schema import BookingCreate, BookingResponse
from app.core.security import dispatcher_or_higher, get_current_user, admin_required
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate

router = APIRouter()


@router.get("", response_model=Page[BookingResponse])
def list_bookings(
        session: Session = Depends(get_session),
        flight_id: int = Query(None),
        passenger_id: int = Query(None),
        _=Depends(get_current_user)
):
    query = select(Booking)
    if flight_id:
        query = query.where(Booking.flight_id == flight_id)
    if passenger_id:
        query = query.where(Booking.passenger_id == passenger_id)

    return paginate(session, query.order_by(Booking.created_at.desc()))


@router.post("", response_model=list[BookingResponse], status_code=status.HTTP_201_CREATED)
def create_bookings(
        data: BookingCreate,
        session: Session = Depends(get_session),
        _=Depends(dispatcher_or_higher)
):
    # Логика продажи билетов (упрощенно для примера)
    flight = session.get(Flight, data.flightId)
    if not flight or flight.free_seats < len(data.passengerIds):
        raise HTTPException(status_code=400, detail="Места отсутствуют или рейс не найден")

    results = []
    code = data.bookingCode or generate_booking_code()

    for p_id in data.passengerIds:
        booking = Booking(
            flight_id=flight.id, 
            passenger_id=p_id, 
            booking_code=code,
            baggage_allowed=data.baggageAllowed,
            payment_type=data.paymentType,
            base_price=data.basePrice,
            tax=data.tax,
            additional_fees=data.additionalFees,
            class_type=data.classType
        )
        session.add(booking)
        results.append(booking)

    flight.free_seats -= len(data.passengerIds)
    session.add(flight)
    session.commit()
    for b in results: session.refresh(b)
    return results


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_booking(booking_id: int, session: Session = Depends(get_session), _=Depends(admin_required)):
    booking = session.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")

    flight = session.get(Flight, booking.flight_id)
    if flight:
        flight.free_seats += 1
        session.add(flight)

    session.delete(booking)
    session.commit()


@router.get("/by-flight/{flight_id}", response_model=List[BookingResponse])
def get_flight_bookings(flight_id: int, session: Session = Depends(get_session), _=Depends(dispatcher_or_higher)):
    bookings = session.exec(select(Booking).where(Booking.flight_id == flight_id)).all()
    return bookings


@router.get("/by-passenger/{passport}", response_model=List[BookingResponse])
def get_passenger_bookings(passport: str, session: Session = Depends(get_session), _=Depends(get_current_user)):
    from app.models.passenger import Passenger
    p = session.exec(select(Passenger).where(Passenger.passport_number == passport)).first()
    if not p:
        raise HTTPException(status_code=404, detail="Пассажир не найден")
    return session.exec(select(Booking).where(Booking.passenger_id == p.id)).all()