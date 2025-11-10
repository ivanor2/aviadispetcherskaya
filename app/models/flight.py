from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import date, time

class Flight(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    flight_number: str
    airline_name: str
    departure_airport_icao: str
    arrival_airport_icao: str
    departure_date: date
    departure_time: time
    total_seats: int
    free_seats: int
