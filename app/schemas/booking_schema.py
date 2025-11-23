from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class BookingCreate(BaseModel):
    """Схема создания бронирования"""
    flightId: int
    passengerId: int


class BookingResponse(BaseModel):
    """Схема ответа с данными бронирования"""
    id: int
    bookingCode: str = Field(alias="booking_code") # Добавлен Field и alias
    flightId: int = Field(alias="flight_id")       # Добавлен Field и alias
    passengerId: int = Field(alias="passenger_id") # Добавлен Field и alias
    createdAt: datetime = Field(alias="created_at") # Добавлен Field и alias