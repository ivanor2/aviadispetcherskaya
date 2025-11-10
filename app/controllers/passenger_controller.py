from sqlmodel import Session, select
from fastapi import HTTPException, status
from app.models.passenger import Passenger
from app.schemas.passenger_schema import PassengerCreate, PassengerUpdate
from typing import List


def create_passenger(data: PassengerCreate, session: Session) -> Passenger:
    """Создание пассажира"""
    existing = session.exec(
        select(Passenger).where(Passenger.passport_number == data.passportNumber)
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пассажир с таким паспортом уже зарегистрирован"
        )

    passenger = Passenger(
        passport_number=data.passportNumber,
        passport_issued_by=data.passportIssuedBy,
        passport_issue_date=data.passportIssueDate,
        full_name=data.fullName,
        birth_date=data.birthDate
    )
    session.add(passenger)
    session.commit()
    session.refresh(passenger)
    return passenger


def get_all_passengers(session: Session) -> List[Passenger]:
    """Получение всех пассажиров"""
    return session.exec(select(Passenger)).all()


def get_passenger_by_id(passenger_id: int, session: Session) -> Passenger:
    """Получение пассажира по ID"""
    passenger = session.get(Passenger, passenger_id)
    if not passenger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пассажир не найден"
        )
    return passenger


def find_passenger_by_passport(passport: str, session: Session) -> Passenger:
    """Поиск пассажира по паспорту"""
    passenger = session.exec(
        select(Passenger).where(Passenger.passport_number == passport)
    ).first()

    if not passenger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пассажир не найден"
        )
    return passenger


def find_passengers_by_name(name: str, session: Session) -> List[Passenger]:
    """Поиск пассажиров по имени"""
    passengers = session.exec(
        select(Passenger).where(Passenger.full_name.contains(name))
    ).all()
    return passengers


def delete_passenger(passenger_id: int, session: Session):
    """Удаление пассажира"""
    passenger = session.get(Passenger, passenger_id)
    if not passenger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пассажир не найден"
        )

    session.delete(passenger)
    session.commit()