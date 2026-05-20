from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from datetime import date, time, datetime
from typing import Optional, List
import re

class FlightCreate(BaseModel):
    flightNumber: str = Field(..., description="Номер рейса в формате AAA-NNN")
    airlineCode: str = Field(..., min_length=3, max_length=3, description="Код авиакомпании")
    departureAirportIcao: str = Field(..., max_length=4)
    arrivalAirportIcao: str = Field(..., max_length=4)
    departureDate: date
    departureTime: time
    arrivalTime: time
    totalSeats: int = Field(..., gt=0)
    freeSeats: int = Field(..., ge=0)

    @field_validator('flightNumber')
    @classmethod
    def validate_flight_number(cls, v):
        if not re.match(r'^[A-Z]{3}-\d{3}$', v.upper()):
            raise ValueError('Номер рейса должен быть строго в формате AAA-NNN')
        return v.upper()

    @field_validator('airlineCode')
    @classmethod
    def validate_airline_code(cls, v):
        return v.upper()

    @model_validator(mode='after')
    def check_prefix_match(self):
        prefix = self.flightNumber.split('-')[0]
        if prefix != self.airlineCode:
            raise ValueError(f'Префикс номера рейса ({prefix}) должен совпадать с кодом авиакомпании ({self.airlineCode})')
        return self

class FlightUpdate(BaseModel):
    flightNumber: Optional[str] = None
    airlineCode: Optional[str] = None
    departureAirportIcao: Optional[str] = None
    arrivalAirportIcao: Optional[str] = None
    departureDate: Optional[date] = None
    departureTime: Optional[time] = None
    arrivalTime: Optional[time] = None
    totalSeats: Optional[int] = None
    freeSeats: Optional[int] = None

class FlightResponse(BaseModel):
    id: int
    flightNumber: str = Field(alias="flight_number")
    airlineCode: str = Field(alias="airline_code") # ✅ Обновлено
    departureAirportIcao: str = Field(alias="departure_airport_icao")
    arrivalAirportIcao: str = Field(alias="arrival_airport_icao")
    departureDate: date = Field(alias="departure_date")
    departureTime: time = Field(alias="departure_time")
    arrivalTime: time = Field(alias="arrival_time")
    totalSeats: int = Field(alias="total_seats")
    freeSeats: int = Field(alias="free_seats")
    model_config = {"from_attributes": True, "populate_by_name": True}


class PassengerBrief(BaseModel):
    full_name: str = Field(alias="full_name")
    passport_number: str = Field(alias="passport_number")
    model_config = ConfigDict(from_attributes=True)

class BookingPassengerResponse(BaseModel):
    id: int
    booking_code: str = Field(alias="booking_code")
    booked_at: datetime = Field(alias="booked_at")
    passenger: PassengerBrief
    model_config = ConfigDict(from_attributes=True)

class FlightWithPassengersResponse(BaseModel):
    flight: FlightResponse
    passengers: List[BookingPassengerResponse]
    model_config = ConfigDict(from_attributes=True)

