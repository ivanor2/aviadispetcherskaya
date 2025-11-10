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