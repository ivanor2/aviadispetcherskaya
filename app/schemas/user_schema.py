from pydantic import BaseModel, Field, field_validator
from fastapi import Form
import re


class UserCreate(BaseModel):
    """Схема создания пользователя"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    role: str = Field(default="dispatcher")

    @field_validator('password')
    def password_complexity(cls, v):
        pattern = r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[!@#$%^&*()_+=-]).{8,}$'
        if not re.match(pattern, v):
            raise ValueError('Пароль должен содержать буквы, цифры и спецсимволы, длина больше 8')
        return v


class UserLogin(BaseModel):
    """Схема авторизации"""
    username: str
    password: str

    @classmethod
    def as_form(
        cls,
        username: str = Form(..., description="Имя пользователя"),
        password: str = Form(..., description="Пароль")
    ):
        return cls(username=username, password=password)


class UserResponse(BaseModel):
    """Схема ответа с данными пользователя"""
    id: int
    username: str
    role: str


class TokenResponse(BaseModel):
    """Схема ответа с токенами"""
    accessToken: str
    refreshToken: str
    tokenType: str = "bearer"
