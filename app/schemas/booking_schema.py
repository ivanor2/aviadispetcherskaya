from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class BookingCreate(BaseModel):
    flightId: int
    passengerIds: List[int] = Field(..., min_length=1, description="ID пассажиров для группового бронирования")
    connectionFlightIds: Optional[List[int]] = Field(default=None, description="ID рейсов для пересадок")
    bookingCode: Optional[str] = Field(None)
    seats: Optional[List[str]] = Field(default=None, description="Номера мест для пассажиров")
    baggageAllowed: bool = Field(default=False, description="Возможность багажа")
    paymentType: str = Field(default="card", description="Тип оплаты: card, cash, online")
    additionalFees: float = Field(default=0.0, description="Дополнительные сборы")
    classType: str = Field(default="economy", description="Класс обслуживания: economy, business, first")

class BookingResponse(BaseModel):
    id: int
    bookingCode: str = Field(alias="booking_code")
    flightId: int = Field(alias="flight_id")
    passengerId: int = Field(alias="passenger_id")
    seat: str = Field(alias="seat")
    createdAt: datetime = Field(alias="created_at")
    baggageAllowed: bool = Field(default=False, alias="baggage_allowed")
    paymentType: str = Field(default="card", alias="payment_type")
    additionalFees: float = Field(default=0.0, alias="additional_fees")
    classType: str = Field(default="economy", alias="class_type", description="Класс обслуживания")
    finalPrice: float = Field(description="Финальная цена", alias="final_price")

    class Config:
        from_attributes = True

class ConnectionAddPayload(BaseModel):
    flightIds: List[int]