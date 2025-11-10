from fastapi import APIRouter, Depends, status, Response
from sqlmodel import Session
from app.db.session import get_session
from app.schemas.booking_schema import BookingCreate, BookingResponse
from app.controllers.booking_controller import *
from app.core.security import get_current_user
from typing import List

router = APIRouter(prefix="/bookings", tags=["Бронирование"])


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def sell_ticket_endpoint(
    data: BookingCreate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Продажа билета"""
    booking = sell_ticket(data.flightId, data.passengerId, session)
    return BookingResponse(
        id=booking.id,
        bookingCode=booking.booking_code,
        flightId=booking.flight_id,
        passengerId=booking.passenger_id,
        createdAt=booking.created_at
    )


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_ticket_endpoint(
    booking_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Отмена продажи билета"""
    cancel_ticket(booking_id, session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/by-flight/{flight_id}", response_model=List[BookingResponse])
def get_bookings_by_flight_endpoint(
    flight_id: int,
    session: Session = Depends(get_session)
):
    """Получение бронирований по рейсу"""
    bookings = get_bookings_by_flight(flight_id, session)
    return [
        BookingResponse(
            id=b.id,
            bookingCode=b.booking_code,
            flightId=b.flight_id,
            passengerId=b.passenger_id,
            createdAt=b.created_at
        )
        for b in bookings
    ]


@router.get("/by-passenger/{passport}", response_model=List[BookingResponse])
def get_bookings_by_passenger_endpoint(
    passport: str,
    session: Session = Depends(get_session)
):
    """Получение бронирований по паспорту пассажира"""
    bookings = get_bookings_by_passenger(passport, session)
    return [
        BookingResponse(
            id=b.id,
            bookingCode=b.booking_code,
            flightId=b.flight_id,
            passengerId=b.passenger_id,
            createdAt=b.created_at
        )
        for b in bookings
    ]