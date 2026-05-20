from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey

def generate_booking_code(length=6):
    import secrets
    import string
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

class Booking(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    booking_code: str
    flight_id: int = Field(foreign_key="flight.id")
    passenger_id: int = Field(
        sa_column=Column(Integer, ForeignKey("passenger.id", ondelete="CASCADE"))
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Новые поля для управления багажом и ценой
    baggage_allowed: bool = Field(default=False, description="Возможность багажа")
    payment_type: str = Field(default="card", description="Тип оплаты: card, cash, online")
    base_price: float = Field(default=0.0, description="Базовая цена")
    tax: float = Field(default=0.0, description="Налог")
    additional_fees: float = Field(default=0.0, description="Дополнительные сборы")
    class_type: str = Field(default="economy", description="Класс обслуживания: economy, business, first")
    
    @property
    def final_price(self) -> float:
        """Вычисляет финальную цену как сумму базовой цены, налога и дополнительных сборов"""
        return self.base_price + self.tax + self.additional_fees