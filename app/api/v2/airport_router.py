from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session, select, col
from app.db.session import get_session
from app.models.airport import Airport
from app.schemas.airport_schema import AirportCreate, AirportUpdate, AirportResponse
from app.core.security import admin_required, get_current_user
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate

router = APIRouter()

@router.get("", response_model=Page[AirportResponse])
def list_airports(session: Session = Depends(get_session), _=Depends(get_current_user),
                  search: str = Query(None), sort_by: str = Query("icao_code"), order: str = Query("asc")):
    q = select(Airport)
    if search: q = q.where(col(Airport.name).ilike(f"%{search}%") | col(Airport.icao_code).ilike(f"%{search}%"))
    order_col = getattr(Airport, sort_by, Airport.icao_code)
    return paginate(session, q.order_by(order_col.asc() if order == "asc" else order_col.desc()))

@router.get("/{airport_id}", response_model=AirportResponse)
def get_airport(airport_id: int, session: Session = Depends(get_session), _=Depends(get_current_user)):
    ap = session.get(Airport, airport_id)
    if not ap: raise status.HTTP_404_NOT_FOUND
    return ap

@router.get("/by-icao/{icao_code}", response_model=AirportResponse)
def get_by_icao(icao_code: str, session: Session = Depends(get_session), _=Depends(get_current_user)):
    ap = session.exec(select(Airport).where(Airport.icao_code == icao_code.upper())).first()
    if not ap: raise status.HTTP_404_NOT_FOUND
    return ap

@router.post("", response_model=AirportResponse, status_code=201, dependencies=[Depends(admin_required)])
def create_airport( AirportCreate, session: Session = Depends(get_session)):
    if session.exec(select(Airport).where(Airport.icao_code == data.icaoCode.upper())).first():
        raise status.HTTP_400_BAD_REQUEST
    ap = Airport(icao_code=data.icaoCode.upper(), name=data.name)
    session.add(ap); session.commit(); session.refresh(ap)
    return ap

@router.put("/{airport_id}", response_model=AirportResponse, dependencies=[Depends(admin_required)])
def update_airport(airport_id: int, data: AirportUpdate, session: Session = Depends(get_session)):
    ap = session.get(Airport, airport_id)
    if not ap: raise status.HTTP_404_NOT_FOUND
    for k, v in data.model_dump(exclude_unset=True).items(): setattr(ap, k, v)
    session.commit(); session.refresh(ap)
    return ap

@router.delete("/{airport_id}", status_code=204, dependencies=[Depends(admin_required)])
def delete_airport(airport_id: int, session: Session = Depends(get_session)):
    ap = session.get(Airport, airport_id)
    if not ap: raise status.HTTP_404_NOT_FOUND
    session.delete(ap); session.commit()