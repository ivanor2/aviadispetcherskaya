# app/api/v1/booking_router.py
from fastapi import APIRouter, Depends, status, Response
from sqlmodel import Session
from app.db.session import get_session
from app.schemas.booking_schema import BookingCreate, BookingResponse
from app.controllers.booking_controller import *
from app.core.security import get_current_user, admin_required
from typing import List

router = APIRouter(prefix="/bookings", tags=["Бронирование"])


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def sell_ticket_endpoint(
    data: BookingCreate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user) # Аутентификация требуется
):
    """Продажа билета"""
    booking = sell_ticket(data, session) # <-- Передаём всю структуру data
    return BookingResponse.model_validate(booking, from_attributes=True)



@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_ticket_endpoint(
    booking_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(admin_required)
):
    """Отмена продажи билета"""
    cancel_ticket(booking_id, session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/by-flight/{flight_id}", response_model=List[BookingResponse], dependencies=[Depends(get_current_user)])
def get_bookings_by_flight_endpoint(
    flight_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user)
):
    """Получение бронирований по рейсу"""
    bookings = get_bookings_by_flight(flight_id, session)
    return [BookingResponse.model_validate(b, from_attributes=True) for b in bookings]



@router.get("/by-passenger/{passport}", response_model=List[BookingResponse])
def get_bookings_by_passenger_endpoint(
    passport: str,
    session: Session = Depends(get_session)
):
    """Получение бронирований по паспорту пассажира"""
    bookings = get_bookings_by_passenger(passport, session)
    return [BookingResponse.model_validate(b, from_attributes=True) for b in bookings]


@router.get("", response_model=List[BookingResponse], dependencies=[Depends(get_current_user)])
def get_all_bookings_endpoint(session: Session = Depends(get_session)):
    """Получение списка всех бронирований (требуется аутентификация)"""
    bookings = get_all_bookings(session)
    return [BookingResponse.model_validate(b, from_attributes=True) for b in bookings]