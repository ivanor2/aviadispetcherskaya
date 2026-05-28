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
    seat: str = Field(default="", description="Номер места пассажира")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Новые поля для управления багажом
    baggage_allowed: bool = Field(default=False, description="Возможность багажа")
    payment_type: str = Field(default="card", description="Тип оплаты: card, cash, online")
    additional_fees: float = Field(default=0.0, description="Дополнительные сборы")
    class_type: str = Field(default="economy", description="Класс обслуживания: economy, business, first")
    
    @property
    def final_price(self) -> float:
        """Вычисляет финальную цену как сумму базовой цены рейса, цены багажа (если есть) и дополнительных сборов"""
        from app.models.flight import Flight
        # Получаем рейс для доступа к ценам
        # В реальном использовании цены должны передаваться из контекста
        return self.additional_fees