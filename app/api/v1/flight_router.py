from fastapi import APIRouter, Depends, status, Response
from sqlmodel import Session

from app.controllers.passenger_controller import create_passenger, get_passenger_by_id, find_passenger_by_passport, \
    find_passengers_by_name, delete_passenger
from app.db.session import get_session
from app.models.passenger import Passenger
from app.schemas.flight_schema import FlightCreate, FlightUpdate, FlightResponse
from app.controllers.flight_controller import *
from app.core.security import get_current_user, admin_required
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate
from typing import List

from app.schemas.passenger_schema import PassengerResponse, PassengerCreate

router = APIRouter(prefix="/flights", tags=["Авиарейсы"])


@router.post("", response_model=PassengerResponse, status_code=status.HTTP_201_CREATED)
def create_passenger_endpoint(
    data: PassengerCreate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Регистрация пассажира"""
    passenger = create_passenger(data, session)
    return PassengerResponse(
        id=passenger.id,
        passportNumber=passenger.passport_number,
        passportIssuedBy=passenger.passport_issued_by,
        passportIssueDate=passenger.passport_issue_date,
        fullName=passenger.full_name,
        birthDate=passenger.birth_date
    )


@router.get("", response_model=Page[PassengerResponse])
def get_passengers_endpoint(session: Session = Depends(get_session)):
    """Просмотр всех пассажиров с пагинацией"""
    return paginate(session, select(Passenger))


@router.get("/{passenger_id}", response_model=PassengerResponse)
def get_passenger_endpoint(passenger_id: int, session: Session = Depends(get_session)):
    """Получение пассажира по ID"""
    passenger = get_passenger_by_id(passenger_id, session)
    return PassengerResponse(
        id=passenger.id,
        passportNumber=passenger.passport_number,
        passportIssuedBy=passenger.passport_issued_by,
        passportIssueDate=passenger.passport_issue_date,
        fullName=passenger.full_name,
        birthDate=passenger.birth_date
    )


@router.get("/search/by-passport/{passport}", response_model=PassengerResponse)
def search_passenger_by_passport(passport: str, session: Session = Depends(get_session)):
    """Поиск пассажира по серии и номеру паспорта"""
    passenger = find_passenger_by_passport(passport, session)
    return PassengerResponse(
        id=passenger.id,
        passportNumber=passenger.passport_number,
        passportIssuedBy=passenger.passport_issued_by,
        passportIssueDate=passenger.passport_issue_date,
        fullName=passenger.full_name,
        birthDate=passenger.birth_date
    )


@router.get("/search/by-name/{name}", response_model=List[PassengerResponse])
def search_passengers_by_name_endpoint(name: str, session: Session = Depends(get_session)):
    """Поиск пассажиров по ФИО"""
    passengers = find_passengers_by_name(name, session)
    return [
        PassengerResponse(
            id=p.id,
            passportNumber=p.passport_number,
            passportIssuedBy=p.passport_issued_by,
            passportIssueDate=p.passport_issue_date,
            fullName=p.full_name,
            birthDate=p.birth_date
        )
        for p in passengers
    ]


@router.delete("/{passenger_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_passenger_endpoint(
    passenger_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(admin_required)
):
    """Удаление пассажира (только для администратора)"""
    delete_passenger(passenger_id, session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
