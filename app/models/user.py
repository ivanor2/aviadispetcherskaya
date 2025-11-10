from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import date


class User(SQLModel, table=True):
    """Модель пользователя"""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, max_length=50)
    password: str = Field(max_length=200)
    role: str = Field(default="dispatcher", max_length=20)
    created_at: date = Field(default_factory=date.today)
