from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.passenger import Passenger
from app.schemas.passenger_schema import PassengerCreate, PassengerUpdate, PassengerResponse
from app.core.security import admin_required, dispatcher_or_higher, get_current_user
from fastapi_pagination import Page
from typing import List

router = APIRouter()

@router.get("", response_model=Page[PassengerResponse])
def list_passengers(session: Session = Depends(get_session), _=Depends(dispatcher_or_higher),
                    search: str = Query(None), sort_by: str = Query("full_name"), order: str = Query("asc")):
    q = select(Passenger)
    if search: q = q.where(Passenger.full_name.ilike(f"%{search}%") | Passenger.passport_number.ilike(f"%{search}%"))
    order_col = getattr(Passenger, sort_by, Passenger.full_name)
    return q.order_by(order_col.asc() if order == "asc" else order_col.desc())

@router.get("/{passenger_id}", response_model=PassengerResponse)
def get_passenger(passenger_id: int, session: Session = Depends(get_session), _=Depends(get_current_user)):
    p = session.get(Passenger, passenger_id)
    if not p: raise status.HTTP_404_NOT_FOUND
    return p

@router.get("/search/by-passport/{passport}", response_model=PassengerResponse)
def search_by_passport(passport: str, session: Session = Depends(get_session), _=Depends(get_current_user)):
    p = session.exec(select(Passenger).where(Passenger.passport_number == passport)).first()
    if not p: raise status.HTTP_404_NOT_FOUND
    return p

@router.get("/search/by-name/{name}", response_model=List[PassengerResponse])
def search_by_name(name: str, session: Session = Depends(get_session), _=Depends(dispatcher_or_higher)):
    return session.exec(select(Passenger).where(Passenger.full_name.contains(name))).all()

@router.post("", response_model=PassengerResponse, status_code=201, dependencies=[Depends(dispatcher_or_higher)])
def create_passenger(data: PassengerCreate, session: Session = Depends(get_session)):
    if session.exec(select(Passenger).where(Passenger.passport_number == data.passportNumber)).first():
        raise status.HTTP_400_BAD_REQUEST
    p = Passenger(**data.model_dump())
    session.add(p); session.commit(); session.refresh(p)
    return p

@router.put("/{passenger_id}", response_model=PassengerResponse, dependencies=[Depends(admin_required)])
def update_passenger(passenger_id: int, data: PassengerUpdate, session: Session = Depends(get_session)):
    p = session.get(Passenger, passenger_id)
    if not p: raise status.HTTP_404_NOT_FOUND
    for k, v in data.model_dump(exclude_unset=True).items(): setattr(p, k, v)
    session.commit(); session.refresh(p)
    return p

@router.delete("/{passenger_id}", status_code=204, dependencies=[Depends(admin_required)])
def delete_passenger(passenger_id: int, session: Session = Depends(get_session)):
    p = session.get(Passenger, passenger_id)
    if not p: raise status.HTTP_404_NOT_FOUND
    session.delete(p); session.commit()