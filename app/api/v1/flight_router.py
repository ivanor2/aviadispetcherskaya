from fastapi import APIRouter, Depends, status, HTTPException, Response
from sqlmodel import Session, select # Добавлен импорт select
from app.db.session import get_session # Исправлен импорт
from app.schemas.flight_schema import FlightCreate, FlightUpdate, FlightResponse
from app.models.flight import Flight
from app.schemas.flight_schema import FlightWithPassengersResponse, PassengerBrief
from app.controllers.flight_controller import (
    create_flight,
    get_all_flights,
    get_flight_by_id,
    get_flight_by_number,
    update_flight,
    delete_flight,
    search_flights_by_arrival,
    get_flight_with_passengers_by_number,
    delete_all_flights
)
from app.core.security import get_current_user, admin_required, dispatcher_or_higher
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate
from typing import List

router = APIRouter(prefix="/flights", tags=["Авиарейсы"])

# --- CRUD для РЕЙСОВ ---
@router.post("", response_model=FlightResponse, status_code=status.HTTP_201_CREATED)
def create_flight_endpoint(
    data: FlightCreate,
    session: Session = Depends(get_session),
    current_user = Depends(dispatcher_or_higher)
):
    """Создание рейса"""
    flight = create_flight(data, session)
    return FlightResponse.model_validate(flight, from_attributes=True)

@router.get("", response_model=Page[FlightResponse]) # Используем Page для пагинации
def get_flights_endpoint(session: Session = Depends(get_session),
                         current_user = Depends(get_current_user)):
    """Просмотр всех рейсов с пагинацией"""
    return paginate(session, select(Flight))

@router.get("/{flight_id}", response_model=FlightResponse)
def get_flight_endpoint(flight_id: int, session: Session = Depends(get_session),
                        current_user = Depends(get_current_user)):
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
def search_flights_by_arrival_endpoint(airport_query: str, session: Session = Depends(get_session),
                                       current_user = Depends(get_current_user)):
    """Поиск рейсов по аэропорту прибытия (частичное совпадение)"""
    flights = search_flights_by_arrival(airport_query, session)
    return [FlightResponse.model_validate(f, from_attributes=True) for f in flights]

@router.get("/by-number/{flight_number}", response_model=FlightWithPassengersResponse)
def get_flight_by_number_with_passengers_endpoint(
    flight_number: str,
    session: Session = Depends(get_session),
    current_user = Depends(dispatcher_or_higher)
):
    """
    Поиск авиарейса по номеру с информацией о пассажирах.
    """
    flight, passengers = get_flight_with_passengers_by_number(flight_number, session)
    flight_response = FlightResponse.model_validate(flight, from_attributes=True)
    passengers_response = [
        PassengerBrief.model_validate(p, from_attributes=True) for p in passengers
    ]
    return FlightWithPassengersResponse(flight=flight_response, passengers=passengers_response)
# ← должен быть импорт

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(admin_required)])
def delete_all_flights_endpoint(
    confirm: bool = False,
    session: Session = Depends(get_session),
    current_user=Depends(admin_required)
):
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Подтвердите удаление: ?confirm=true"
        )
    delete_all_flights(session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)