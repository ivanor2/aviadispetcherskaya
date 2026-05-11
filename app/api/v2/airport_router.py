from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlmodel import Session, select, col, or_
from app.db.session import get_session
from app.models.airport import Airport
from app.schemas.airport_schema import AirportCreate, AirportUpdate, AirportResponse
from app.core.security import admin_required, get_current_user
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate

router = APIRouter()


@router.get("", response_model=Page[AirportResponse])
def list_airports(
        session: Session = Depends(get_session),
        search: str = Query(None),
        sort_by: str = Query("icao_code"),
        order: str = Query("asc"),
        _=Depends(get_current_user)
):
    query = select(Airport)
    if search:
        query = query.where(
            or_(
                col(Airport.name).ilike(f"%{search}%"),
                col(Airport.icao_code).ilike(f"%{search}%")
            )
        )

    # Маппинг для сортировки (обработка camelCase из запроса в snake_case модели)
    attr_map = {"icaoCode": "icao_code", "name": "name"}
    sort_attr = attr_map.get(sort_by, sort_by)
    column = getattr(Airport, sort_attr, Airport.icao_code)

    query = query.order_by(column.asc() if order == "asc" else column.desc())
    return paginate(session, query)


@router.post("", response_model=AirportResponse, status_code=201, dependencies=[Depends(admin_required)])
def create_airport(data: AirportCreate, session: Session = Depends(get_session)):
    if session.exec(select(Airport).where(Airport.icao_code == data.icaoCode.upper())).first():
        raise HTTPException(status_code=400, detail="ICAO код уже занят")
    ap = Airport(icao_code=data.icaoCode.upper(), name=data.name)
    session.add(ap)
    session.commit()
    session.refresh(ap)
    return ap