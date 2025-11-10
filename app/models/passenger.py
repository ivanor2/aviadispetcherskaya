from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import date

class Passenger(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    passport_number: str
    passport_issued_by: str
    passport_issue_date: date
    full_name: str
    birth_date: date
