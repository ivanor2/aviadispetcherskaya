from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import date, time


class Flight(SQLModel, table=True):
    __tablename__ = "flight"
    id: Optional[int] = Field(default=None, primary_key=True)
    flight_number: str = Field(unique=True, index=True)

    airline_code: str = Field(max_length=3, foreign_key="airline.code")

    departure_airport_icao: str = Field(foreign_key="airport.icao_code", max_length=4)
    arrival_airport_icao: str = Field(foreign_key="airport.icao_code", max_length=4)
    departure_date: date
    departure_time: time
    arrival_time: time
    total_seats: int
    free_seats: int