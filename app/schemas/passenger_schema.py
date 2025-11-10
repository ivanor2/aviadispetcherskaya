from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Optional
import re


class PassengerCreate(BaseModel):
    """Схема создания пассажира"""
    passportNumber: str = Field(..., description="Номер паспорта NNNN-NNNNNN")
    passportIssuedBy: str = Field(..., max_length=200)
    passportIssueDate: date
    fullName: str = Field(..., max_length=200)
    birthDate: date

    @field_validator('passportNumber')
    def validate_passport(cls, v):
        pattern = r'^\d{4}-\d{6}$'
        if not re.match(pattern, v):
            raise ValueError('Номер паспорта должен быть в формате NNNN-NNNNNN')
        return v


class PassengerUpdate(BaseModel):
    """Схема обновления пассажира"""
    passportNumber: Optional[str] = None
    passportIssuedBy: Optional[str] = None
    passportIssueDate: Optional[date] = None
    fullName: Optional[str] = None
    birthDate: Optional[date] = None


class PassengerResponse(BaseModel):
    """Схема ответа с данными пассажира"""
    id: int
    passportNumber: str
    passportIssuedBy: str
    passportIssueDate: date
    fullName: str
    birthDate: date