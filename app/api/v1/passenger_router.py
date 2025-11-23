# app/api/v1/passenger_router.py

# ... (остальные импорты)
from fastapi import APIRouter, Depends, status, HTTPException
from sqlmodel import Session, select
from typing import List

from app.db.session import get_session
from app.schemas.passenger_schema import (
    PassengerCreate,
    PassengerUpdate,
    PassengerResponse,
)
from app.models.passenger import Passenger
from app.controllers.passenger_controller import (
    create_passenger as ctrl_create_passenger,
    get_all_passengers as ctrl_get_all_passengers,
    get_passenger_by_id as ctrl_get_passenger_by_id,
    find_passenger_by_passport as ctrl_find_passenger_by_passport,
    find_passengers_by_name as ctrl_find_passengers_by_name,
    delete_passenger as ctrl_delete_passenger,
    update_passenger as ctrl_update_passenger # Добавлен импорт
)
from app.core.security import get_current_user, admin_required
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate

router = APIRouter(prefix="/passengers", tags=["Пассажиры"])


@router.post("", response_model=PassengerResponse, status_code=status.HTTP_201_CREATED)
def create_passenger_endpoint(
    data: PassengerCreate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user) # Аутентификация требуется
):
    """Регистрация пассажира."""
    # Проверка на дубликат паспорта может быть в контроллере
    passenger = ctrl_create_passenger(data, session)
    # Возвращаем объект модели, Pydantic сам сопоставит поля через alias и from_attributes
    return PassengerResponse.model_validate(passenger, from_attributes=True)


@router.get("", response_model=Page[PassengerResponse]) # Используем Page для пагинации
def get_passengers_endpoint(
    session: Session = Depends(get_session),
):
    """Просмотр всех пассажиров с пагинацией."""
    return paginate(session, select(Passenger))


@router.get("/{passenger_id}", response_model=PassengerResponse)
def get_passenger_endpoint(
    passenger_id: int,
    session: Session = Depends(get_session),
):
    """Получение пассажира по ID."""
    passenger = ctrl_get_passenger_by_id(passenger_id, session)
    return PassengerResponse.model_validate(passenger, from_attributes=True)


@router.get("/search/by-passport/{passport}", response_model=PassengerResponse)
def search_passenger_by_passport_endpoint(
    passport: str,
    session: Session = Depends(get_session),
):
    """Поиск пассажира по серии и номеру паспорта."""
    passenger = ctrl_find_passenger_by_passport(passport, session)
    if not passenger:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пассажир не найден")
    # Возвращаем объект модели, Pydantic сам сопоставит поля через alias и from_attributes
    return PassengerResponse.model_validate(passenger, from_attributes=True)


@router.get("/search/by-name/{name}", response_model=List[PassengerResponse])
def search_passengers_by_name_endpoint(
    name: str,
    session: Session = Depends(get_session),
):
    """Поиск пассажиров по ФИО (частичное совпадение)."""
    passengers = ctrl_find_passengers_by_name(name, session)
    return [PassengerResponse.model_validate(p, from_attributes=True) for p in passengers]


@router.put("/{passenger_id}", response_model=PassengerResponse)
def update_passenger_endpoint(
    passenger_id: int,
    data: PassengerUpdate, # <-- Убедитесь, что параметр называется 'data'
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user) # Аутентификация требуется
):
    """Обновление данных пассажира по ID."""
    passenger = ctrl_update_passenger(passenger_id, data, session) # <-- Используем 'data'
    if not passenger:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пассажир не найден")
    return PassengerResponse.model_validate(passenger, from_attributes=True)


@router.delete("/{passenger_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_passenger_endpoint(
    passenger_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(admin_required) # Требуется роль администратора
):
    """Удаление пассажира по ID (только для администратора)."""
    success = ctrl_delete_passenger(passenger_id, session)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пассажир не найден")
    return
