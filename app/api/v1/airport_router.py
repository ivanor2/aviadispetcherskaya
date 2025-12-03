# app/api/v1/airport_router.py

from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from app.db.session import get_session
from app.schemas.airport_schema import AirportCreate, AirportUpdate, AirportResponse
from app.controllers.airport_controller import (
    get_all_airports,
    get_airport_by_id,
    get_airport_by_icao,
    create_airport,
    update_airport,
    delete_airport
)
from app.core.security import admin_required, get_current_user
from typing import List

router = APIRouter(prefix="/airports", tags=["Аэропорты"])

@router.get("", response_model=List[AirportResponse])
def get_airports_list(session: Session = Depends(get_session)):
    """
    Получение списка всех аэропортов (id, ИКАО и название).
    """
    airports = get_all_airports(session)
    return [AirportResponse.model_validate(a, from_attributes=True) for a in airports]

@router.get("/{airport_id}", response_model=AirportResponse)
def get_airport_by_id_endpoint(airport_id: int, session: Session = Depends(get_session)):
    """
    Получение аэропорта по ID.
    """
    airport = get_airport_by_id(airport_id, session)
    return AirportResponse.model_validate(airport, from_attributes=True)

@router.get("/by-icao/{icao_code}", response_model=AirportResponse)
def get_airport_by_icao_endpoint(icao_code: str, session: Session = Depends(get_session)):
    """
    Получение аэропорта по ICAO-коду.
    """
    airport = get_airport_by_icao(icao_code, session)
    return AirportResponse.model_validate(airport, from_attributes=True)

@router.post("", response_model=AirportResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(admin_required)])
def create_airport_endpoint(
    data: AirportCreate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    Создание нового аэропорта (только для администратора).
    """
    airport = create_airport(data, session)
    return AirportResponse.model_validate(airport, from_attributes=True)

@router.put("/{airport_id}", response_model=AirportResponse, dependencies=[Depends(admin_required)])
def update_airport_endpoint(
    airport_id: int,
    data: AirportUpdate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    Обновление аэропорта по ID (только для администратора).
    """
    airport = update_airport(airport_id, data, session)
    return AirportResponse.model_validate(airport, from_attributes=True)

@router.delete("/{airport_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(admin_required)])
def delete_airport_endpoint(
    airport_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """
    Удаление аэропорта по ID (только для администратора).
    """
    delete_airport(airport_id, session)
    return # 204 No Content