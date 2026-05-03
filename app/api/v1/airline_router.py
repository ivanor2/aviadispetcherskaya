from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from app.db.session import get_session
from app.schemas.airline_schema import AirlineCreate, AirlineResponse
import app.controllers.airline_controller as ctrl
from app.core.security import admin_required, get_current_user
from typing import List

router = APIRouter(prefix="", tags=["Авиакомпании"])

@router.get("", response_model=List[AirlineResponse])
def list_airlines(session: Session = Depends(get_session), _=Depends(get_current_user)):
    return ctrl.get_all_airlines(session)

@router.get("/{code}", response_model=AirlineResponse)
def get_airline(code: str, session: Session = Depends(get_session), _=Depends(get_current_user)):
    return ctrl.get_airline_by_code(code, session)

@router.post("", response_model=AirlineResponse, status_code=status.HTTP_201_CREATED)
def create_airline(data: AirlineCreate, session: Session = Depends(get_session), _=Depends(admin_required)):
    return ctrl.create_airline(data, session)

@router.put("/{code}", response_model=AirlineResponse)
def update_airline(code: str, data: AirlineCreate, session: Session = Depends(get_session), _=Depends(admin_required)):
    return ctrl.update_airline(code, data, session)

@router.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_airline(code: str, session: Session = Depends(get_session), _=Depends(admin_required)):
    ctrl.delete_airline(code, session)