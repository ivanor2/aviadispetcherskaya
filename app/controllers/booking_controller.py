from sqlmodel import Session, select
from fastapi import HTTPException, status
from app.models.booking import Booking, generate_booking_code
from app.models.flight import Flight
from app.models.passenger import Passenger
from typing import List


def sell_ticket(flight_id: int, passenger_id: int, session: Session) -> Booking:
    """Продажа билета"""
    flight = session.get(Flight, flight_id)
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

    passenger = session.get(Passenger, passenger_id)
    if not passenger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пассажир не найден"
        )

    # Проверка на дубликат бронирования
    existing_booking = session.exec(
        select(Booking).where(
            Booking.flight_id == flight_id,
            Booking.passenger_id == passenger_id
        )
    ).first()

    if existing_booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Билет уже куплен"
        )

    booking = Booking(
        booking_code=generate_booking_code(),
        flight_id=flight_id,
        passenger_id=passenger_id
    )

    flight.free_seats -= 1
    session.add(booking)
    session.add(flight)
    session.commit()
    session.refresh(booking)

    return booking


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