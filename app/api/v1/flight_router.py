from fastapi import APIRouter, Depends, status, HTTPException, Response
from sqlmodel import Session, select # Добавлен импорт select
from app.db.session import get_session # Исправлен импорт
from app.schemas.flight_schema import FlightCreate, FlightUpdate, FlightResponse
from app.models.flight import Flight # Добавлен импорт модели Flight
from app.controllers.flight_controller import (
    create_flight,
    get_all_flights,
    get_flight_by_id,
    get_flight_by_number,
    update_flight,
    delete_flight,
    search_flights_by_arrival
)
from app.core.security import get_current_user, admin_required
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate
from typing import List

router = APIRouter(prefix="/flights", tags=["Авиарейсы"])

# --- CRUD для РЕЙСОВ ---
@router.post("", response_model=FlightResponse, status_code=status.HTTP_201_CREATED)
def create_flight_endpoint(
    data: FlightCreate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Создание рейса"""
    flight = create_flight(data, session)
    return FlightResponse.model_validate(flight, from_attributes=True)

@router.get("", response_model=Page[FlightResponse]) # Используем Page для пагинации
def get_flights_endpoint(session: Session = Depends(get_session)):
    """Просмотр всех рейсов с пагинацией"""
    return paginate(session, select(Flight))

@router.get("/{flight_id}", response_model=FlightResponse)
def get_flight_endpoint(flight_id: int, session: Session = Depends(get_session)):
    """Получение рейса по ID"""
    flight = get_flight_by_id(flight_id, session)
    # Возвращаем объект модели, Pydantic сам сопоставит поля через alias и from_attributes
    return FlightResponse.model_validate(flight, from_attributes=True)

@router.put("/{flight_id}", response_model=FlightResponse)
def update_flight_endpoint(
    flight_id: int,
    data: FlightUpdate,
    session: Session = Depends(get_session),
    current_user=Depends(admin_required)
 # Аутентификация требуется
):
    """Обновление рейса по ID"""
    flight = update_flight(flight_id, data, session)
    if not flight:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рейс не найден")
    return FlightResponse.model_validate(flight, from_attributes=True)

@router.delete("/{flight_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flight_endpoint(
    flight_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(admin_required)
):
    """Удаление рейса по ID (только для администратора)"""
    delete_flight(flight_id, session)
    return # 204 No Content

# --- Поиск ---
@router.get("/search/by-arrival/{airport_query}", response_model=List[FlightResponse])
def search_flights_by_arrival_endpoint(airport_query: str, session: Session = Depends(get_session)):
    """Поиск рейсов по аэропорту прибытия (частичное совпадение)"""
    flights = search_flights_by_arrival(airport_query, session)
    return [FlightResponse.model_validate(f, from_attributes=True) for f in flights]