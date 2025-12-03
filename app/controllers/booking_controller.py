# app/controllers/booking_controller.py
from sqlmodel import Session, select
from fastapi import HTTPException, status
from app.models.booking import Booking, generate_booking_code
from app.models.flight import Flight
from app.models.passenger import Passenger
from typing import List
from app.schemas.booking_schema import BookingCreate # <-- Импортируем схему


def sell_ticket(data: BookingCreate, session: Session) -> Booking: # <-- Принимаем BookingCreate
    """Продажа билета"""
    flight = session.get(Flight, data.flightId) # <-- Используем data.flightId
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Рейс не найден"
        )

    if flight.free_seats <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нет свободных мест"
        )

    passenger = session.get(Passenger, data.passengerId) # <-- Используем data.passengerId
    if not passenger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
             detail="Пассажир не найден"
        )

    # Проверка на дубликат бронирования
    existing_booking = session.exec(
        select(Booking).where(
            Booking.flight_id == data.flightId, # <-- Используем data.flightId
            Booking.passenger_id == data.passengerId # <-- Используем data.passengerId
        )
    ).first()

    if existing_booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Билет уже куплен"
        )

    # --- ОПРЕДЕЛЕНИЕ booking_code ---
    booking_code_to_use = data.bookingCode # <-- Извлекаем bookingCode из данных
    if booking_code_to_use is None:
        booking_code_to_use = generate_booking_code() # <-- Генерируем, если не задан
    # --- /ОПРЕДЕЛЕНИЕ booking_code ---

    booking = Booking(
        booking_code=booking_code_to_use, # <-- Используем выбранный код
        flight_id=data.flightId, # <-- Используем data.flightId
        passenger_id=data.passengerId # <-- Используем data.passengerId
    )

    flight.free_seats -= 1
    session.add(booking)
    session.add(flight)
    session.commit()
    session.refresh(booking)

    return booking


# --- (остальные функции остаются без изменений) ---

def cancel_ticket(booking_id: int, session: Session):
    """Отмена билета"""
    booking = session.get(Booking, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Бронирование не найдено"
        )

    flight = session.get(Flight, booking.flight_id)
    if flight:
        flight.free_seats += 1
        session.add(flight)

    session.delete(booking)
    session.commit()


def get_bookings_by_flight(flight_id: int, session: Session) -> List[Booking]:
    """Получение бронирований по рейсу"""
    return session.exec(
        select(Booking).where(Booking.flight_id == flight_id)
    ).all()


def get_bookings_by_passenger(passport: str, session: Session) -> List[Booking]:
    """Получение бронирований пассажира"""
    passenger = session.exec(
        select(Passenger).where(Passenger.passport_number == passport)
    ).first()

    if not passenger:
        return []

    return session.exec(
        select(Booking).where(Booking.passenger_id == passenger.id)
    ).all()

def get_all_bookings(session: Session) -> List[Booking]:
    """Получение всех бронирований"""
    return session.exec(select(Booking)).all()