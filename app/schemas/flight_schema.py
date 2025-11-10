from pydantic import BaseModel, Field, field_validator
from datetime import date, time
from typing import Optional
import re


class FlightCreate(BaseModel):
    """Схема создания рейса"""
    flightNumber: str = Field(..., description="Номер рейса в формате AAA-NNN")
    airlineName: str = Field(..., max_length=100)
    departureAirportIcao: str = Field(..., min_length=4, max_length=4)
    arrivalAirportIcao: str = Field(..., min_length=4, max_length=4)
    departureDate: date
    departureTime: time
    totalSeats: int = Field(..., gt=0)
    freeSeats: int = Field(..., ge=0)

    @field_validator('flightNumber')
    def validate_flight_number(cls, v):
        pattern = r'^[A-Z]{2,3}-\d{3}$'
        if not re.match(pattern, v):
            raise ValueError('Номер рейса должен быть в формате AAA-NNN')
        return v


class FlightUpdate(BaseModel):
    """Схема обновления рейса"""
    flightNumber: Optional[str] = None
    airlineName: Optional[str] = None
    departureAirportIcao: Optional[str] = None
    arrivalAirportIcao: Optional[str] = None
    departureDate: Optional[date] = None
    departureTime: Optional[time] = None
    totalSeats: Optional[int] = None
    freeSeats: Optional[int] = None


class FlightResponse(BaseModel):
    """Схема ответа с данными рейса"""
    id: int
    flightNumber: str
    airlineName: str
    departureAirportIcao: str
    arrivalAirportIcao: str
    departureDate: date
    departureTime: time
    totalSeats: int
    freeSeats: int