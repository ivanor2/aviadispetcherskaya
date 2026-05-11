from typing import List

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlmodel import Session, select, or_, col
from app.db.session import get_session
from app.models.booking import Booking
from app.models.passenger import Passenger
from app.schemas.booking_schema import BookingResponse
from app.schemas.passenger_schema import PassengerCreate, PassengerUpdate, PassengerResponse
from app.core.security import dispatcher_or_higher, get_current_user
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate

router = APIRouter()


@router.get("", response_model=Page[PassengerResponse])
def list_passengers(
    session: Session = Depends(get_session),
    search: str = Query(None),
    _=Depends(get_current_user)
):
    query = select(Passenger)
    if search:
        query = query.where(
            or_(
                col(Passenger.full_name).ilike(f"%{search}%"),
                col(Passenger.passport_number).contains(search)
            )
        )
    return paginate(session, query.order_by(Passenger.full_name))


@router.get("/{passenger_id}", response_model=PassengerResponse)
def get_passenger(passenger_id: int, session: Session = Depends(get_session), _=Depends(get_current_user)):
    p = session.get(Passenger, passenger_id)
    if not p:
        raise HTTPException(status_code=404, detail="Пассажир не найден")
    return p


@router.post("", response_model=PassengerResponse, status_code=201)
def create_passenger(data: PassengerCreate, session: Session = Depends(get_session), _=Depends(dispatcher_or_higher)):
    if session.exec(select(Passenger).where(Passenger.passport_number == data.passportNumber)).first():
        raise HTTPException(status_code=400, detail="Duplicate passport")

    p = Passenger(
        passport_number=data.passportNumber,
        full_name=data.fullName,
        birth_date=data.birthDate,
        passport_issued_by=data.passportIssuedBy,
        passport_issue_date=data.passportIssueDate
    )
    session.add(p)
    session.commit()
    session.refresh(p)
    return p
