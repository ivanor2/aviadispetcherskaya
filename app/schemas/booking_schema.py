from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class BookingCreate(BaseModel):
    flightId: int
    passengerIds: List[int] = Field(..., min_length=1, description="ID пассажиров для группового бронирования")
    connectionFlightIds: Optional[List[int]] = Field(default=None, description="ID рейсов для пересадок")
    bookingCode: Optional[str] = Field(None)

class BookingResponse(BaseModel):
    id: int
    bookingCode: str = Field(alias="booking_code")
    flightId: int = Field(alias="flight_id")
    passengerId: int = Field(alias="passenger_id")
    createdAt: datetime = Field(alias="created_at")

    class Config:
        from_attributes = True

class ConnectionAddPayload(BaseModel):
    flightIds: List[int]