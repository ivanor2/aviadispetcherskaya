from sqlmodel import Session, select
from fastapi import HTTPException, status
from app.models.airline import Airline
from app.schemas.airline_schema import AirlineCreate
from typing import List


def get_all_airlines(session: Session) -> List[Airline]:
    return session.exec(select(Airline)).all()


def get_airline_by_code(code: str, session: Session) -> Airline:
    airline = session.get(Airline, code.upper())
    if not airline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Авиакомпания не найдена")
    return airline


def create_airline(data: AirlineCreate, session: Session) -> Airline:
    existing = session.get(Airline, data.code)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Авиакомпания с таким кодом уже существует")

    airline = Airline(code=data.code, name=data.name)
    session.add(airline)
    session.commit()
    session.refresh(airline)
    return airline


def update_airline(code: str, data: AirlineCreate, session: Session) -> Airline:
    airline = session.get(Airline, code.upper())
    if not airline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Авиакомпания не найдена")
    airline.name = data.name
    session.commit()
    session.refresh(airline)
    return airline


def delete_airline(code: str, session: Session):
    airline = session.get(Airline, code.upper())
    if not airline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Авиакомпания не найдена")
    session.delete(airline)
    session.commit()