# app/controllers/booking_controller.py
from sqlmodel import Session, select
from fastapi import HTTPException, status
from app.models.booking import Booking, generate_booking_code
from app.models.flight import Flight
from app.models.passenger import Passenger
from typing import List
from app.schemas.booking_schema import BookingCreate # <-- Импортируем схему


def sell_ticket(data: BookingCreate, session: Session) -> List[Booking]:
    p_count = len(data.passengerIds)

    # 1. Проверка основного рейса и мест
    flight = session.get(Flight, data.flightId)
    if not flight:
        raise HTTPException(status_code=404, detail="Основной рейс не найден")
    if flight.free_seats < p_count:
        raise HTTPException(status_code=400, detail="Недостаточно мест на основном рейсе")

    # 2. Проверка пассажиров
    passengers = session.exec(select(Passenger).where(Passenger.id.in_(data.passengerIds))).all()
    if len(passengers) != p_count:
        raise HTTPException(status_code=400, detail="Один или несколько пассажиров не найдены")

    # 3. Проверка дубликатов на основной рейс
    existing = session.exec(select(Booking).where(
        Booking.flight_id == data.flightId,
        Booking.passenger_id.in_(data.passengerIds)
    )).all()
    if existing:
        raise HTTPException(status_code=400, detail="Билет уже куплен для одного из пассажиров на этот рейс")

    booking_code = data.bookingCode or generate_booking_code()

    # 4. Проверка рейсов пересадки
    connection_flights = []
    if data.connectionFlightIds:
        for fid in data.connectionFlightIds:
            cf = session.get(Flight, fid)
            if not cf:
                raise HTTPException(status_code=404, detail=f"Рейс пересадки {fid} не найден")
            if cf.free_seats < p_count:
                raise HTTPException(status_code=400, detail=f"Недостаточно мест на рейсе пересадки {cf.flight_number}")

            dup_cf = session.exec(select(Booking).where(
                Booking.flight_id == fid,
                Booking.passenger_id.in_(data.passengerIds)
            )).all()
            if dup_cf:
                raise HTTPException(status_code=400, detail=f"Пассажир уже имеет билет на рейс {cf.flight_number}")
            connection_flights.append(cf)

    try:
        created_bookings = []
        for p_id in data.passengerIds:
            created_bookings.append(Booking(booking_code=booking_code, flight_id=data.flightId, passenger_id=p_id))
            for cf in connection_flights:
                created_bookings.append(Booking(booking_code=booking_code, flight_id=cf.id, passenger_id=p_id))

        # Списание мест
        flight.free_seats -= p_count
        session.add(flight)
        for cf in connection_flights:
            cf.free_seats -= p_count
            session.add(cf)

        session.add_all(created_bookings)
        session.commit()
        for b in created_bookings:
            session.refresh(b)
        return created_bookings
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при создании бронирования: {str(e)}")


def add_connections_to_booking(booking_code: str, flight_ids: List[int], session: Session) -> List[Booking]:
    existing = session.exec(select(Booking).where(Booking.booking_code == booking_code)).all()
    if not existing:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")

    passenger_ids = list(set(b.passenger_id for b in existing))
    p_count = len(passenger_ids)

    try:
        new_bookings = []
        for fid in flight_ids:
            flight = session.get(Flight, fid)
            if not flight:
                raise HTTPException(status_code=404, detail=f"Рейс {fid} не найден")
            if flight.free_seats < p_count:
                raise HTTPException(status_code=400, detail=f"Недостаточно мест на рейсе {flight.flight_number}")

            dup = session.exec(select(Booking).where(
                Booking.flight_id == fid,
                Booking.passenger_id.in_(passenger_ids)
            )).all()
            if dup:
                raise HTTPException(status_code=400, detail="Один из пассажиров уже имеет билет на этот рейс")

            for p_id in passenger_ids:
                new_bookings.append(Booking(booking_code=booking_code, flight_id=fid, passenger_id=p_id))

            flight.free_seats -= p_count
            session.add(flight)

        session.add_all(new_bookings)
        session.commit()
        for b in new_bookings:
            session.refresh(b)
        return new_bookings
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


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
