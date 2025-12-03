# app/models/airport.py

from sqlmodel import SQLModel, Field
from typing import Optional

class Airport(SQLModel, table=True):
    __tablename__ = "airport"
    id: Optional[int] = Field(default=None, primary_key=True)
    icao_code: str = Field(index=True, unique=True, max_length=4) # Уникальный индекс на ICAO
    name: Optional[str] = Field(default=None, max_length=200)