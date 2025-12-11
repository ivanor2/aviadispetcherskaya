from pydantic import BaseModel, Field, field_validator
from datetime import date, time
from typing import Optional
import re


class FlightCreate(BaseModel):
    """Схема создания рейса"""
    flightNumber: str = Field(..., description="Номер рейса в формате AAA-NNN", examples=["111-AAA"])
    airlineName: str = Field(..., max_length=100)
    departureAirportId: int  # Изменено: теперь принимает ID
    arrivalAirportId: int    # Изменено: теперь принимает ID
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

    # Валидаторы для ID аэропортов (опционально, но рекомендуется)
    @field_validator('departureAirportId', 'arrivalAirportId')
    def validate_airport_id(cls, v):
        if v <= 0:
            raise ValueError('ID аэропорта должен быть положительным целым числом')
        return v

class FlightUpdate(BaseModel):
    """Схема обновления рейса"""
    flightNumber: Optional[str] = None
    airlineName: Optional[str] = None
    departureAirportId: Optional[int] = None # Изменено: теперь ID
    arrivalAirportId: Optional[int] = None   # Изменено: теперь ID
    departureDate: Optional[date] = None
    departureTime: Optional[time] = None
    totalSeats: Optional[int] = None
    freeSeats: Optional[int] = None

    # Валидаторы для ID аэропортов (опционально, но рекомендуется)
    @field_validator('departureAirportId', 'arrivalAirportId')
    def validate_airport_id(cls, v):
        if v is not None and v <= 0: # Проверяем только если значение передано
            raise ValueError('ID аэропорта должен быть положительным целым числом')
        return v


class FlightResponse(BaseModel):
    """Схема ответа с данными рейса"""
    id: int
    flightNumber: str = Field(alias="flight_number")
    airlineName: str = Field(alias="airline_name")
    departureAirportId: int = Field(alias="departure_airport_id") # Изменено: теперь ID
    arrivalAirportId: int = Field(alias="arrival_airport_id")     # Изменено: теперь ID
    departureDate: date = Field(alias="departure_date")
    departureTime: time = Field(alias="departure_time")
    totalSeats: int = Field(alias="total_seats")
    freeSeats: int = Field(alias="free_seats")

    class Config:
        from_attributes = True

# app/schemas/flight_schema.py

# (в конце файла)

class PassengerBrief(BaseModel):
    fullName: str = Field(alias="full_name")
    passportNumber: str = Field(alias="passport_number")

    class Config:
        from_attributes = True


class FlightWithPassengersResponse(BaseModel):
    flight: FlightResponse
    passengers: list[PassengerBrief]

    class Config:
        from_attributes = True