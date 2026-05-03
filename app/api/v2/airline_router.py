from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.airline import Airline
from app.schemas.airline_schema import AirlineCreate, AirlineResponse
from app.core.security import admin_required, get_current_user
from fastapi_pagination import Page

router = APIRouter()

@router.get("", response_model=Page[AirlineResponse])
def list_airlines(session: Session = Depends(get_session), _=Depends(get_current_user),
                  search: str = Query(None), sort_by: str = Query("code"), order: str = Query("asc")):
    q = select(Airline)
    if search: q = q.where(Airline.name.ilike(f"%{search}%") | Airline.code.ilike(f"%{search}%"))
    order_col = getattr(Airline, sort_by, Airline.code)
    return q.order_by(order_col.asc() if order == "asc" else order_col.desc())

@router.get("/{code}", response_model=AirlineResponse)
def get_airline(code: str, session: Session = Depends(get_session), _=Depends(get_current_user)):
    al = session.get(Airline, code.upper())
    if not al: raise status.HTTP_404_NOT_FOUND
    return al

@router.post("", response_model=AirlineResponse, status_code=201, dependencies=[Depends(admin_required)])
def create_airline(data: AirlineCreate, session: Session = Depends(get_session)):
    al = Airline(code=data.code.upper(), name=data.name)
    session.add(al); session.commit(); session.refresh(al)
    return al

@router.put("/{code}", response_model=AirlineResponse, dependencies=[Depends(admin_required)])
def update_airline(code: str, data: AirlineCreate, session: Session = Depends(get_session)):
    al = session.get(Airline, code.upper())
    if not al: raise status.HTTP_404_NOT_FOUND
    al.name = data.name
    session.commit(); session.refresh(al)
    return al

@router.delete("/{code}", status_code=204, dependencies=[Depends(admin_required)])
def delete_airline(code: str, session: Session = Depends(get_session)):
    al = session.get(Airline, code.upper())
    if not al: raise status.HTTP_404_NOT_FOUND
    session.delete(al); session.commit()