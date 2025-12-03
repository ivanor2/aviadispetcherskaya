# app/schemas/booking_schema.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class BookingCreate(BaseModel):
    """Схема создания бронирования"""
    flightId: int
    passengerId: int
    bookingCode: Optional[str] = Field(None) # <-- Опциональное поле


class BookingResponse(BaseModel):
    """Схема ответа с данными бронирования"""
    id: int
    bookingCode: str = Field(alias="booking_code")
    flightId: int = Field(alias="flight_id")
    passengerId: int = Field(alias="passenger_id")
    createdAt: datetime = Field(alias="created_at")