# app/controllers/airport_controller.py

from sqlmodel import Session, select
from fastapi import HTTPException, status
from app.models.airport import Airport
from app.schemas.airport_schema import AirportCreate, AirportUpdate
from typing import List

def get_all_airports(session: Session) -> List[Airport]:
    """
    Возвращает список всех аэропортов (id, ИКАО и название) из БД.
    """
    airports_db = session.exec(select(Airport)).all()
    return airports_db

def get_airport_by_id(airport_id: int, session: Session) -> Airport:
    """
    Возвращает аэропорт по его ID.
    """
    airport = session.get(Airport, airport_id)
    if not airport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аэропорт не найден"
        )
    return airport

def get_airport_by_icao(icao_code: str, session: Session) -> Airport:
    """
    Проверяет существование аэропорта по официальному ИКАО-коду в БД и возвращает его.
    """
    airport = session.exec(
        select(Airport).where(Airport.icao_code == icao_code.upper())
    ).first()
    if not airport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аэропорт с таким ICAO-кодом не найден"
        )
    return airport

def create_airport(data: AirportCreate, session: Session) -> Airport:
    """
    Создаёт новый аэропорт.
    """
    # Проверка на дубликат ICAO
    existing = session.exec(
        select(Airport).where(Airport.icao_code == data.icaoCode.upper())
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Аэропорт с таким ICAO-кодом уже существует"
        )

    airport = Airport(
        icao_code=data.icaoCode.upper(), # Сохраняем в верхнем регистре для консистентности
        name=data.name
    )
    session.add(airport)
    session.commit()
    session.refresh(airport)
    return airport

def update_airport(airport_id: int, data: AirportUpdate, session: Session) -> Airport:
    """
    Обновляет аэропорт по ID.
    """
    airport = session.get(Airport, airport_id)
    if not airport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аэропорт не найден"
        )

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(airport, key, value)

    session.add(airport)
    session.commit()
    session.refresh(airport)
    return airport

def delete_airport(airport_id: int, session: Session):
    """
    Удаляет аэропорт по ID.
    """
    airport = session.get(Airport, airport_id)
    if not airport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аэропорт не найден"
        )

    session.delete(airport)
    session.commit()