from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class BookingCreate(BaseModel):
    """Схема создания бронирования"""
    flightId: int
    passengerId: int


class BookingResponse(BaseModel):
    """Схема ответа с данными бронирования"""
    id: int
    bookingCode: str
    flightId: int
    passengerId: int
    createdAt: datetime