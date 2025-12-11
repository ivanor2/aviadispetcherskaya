# app/api/v1/auth_router.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from pydantic import ValidationError
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.user import User
from app.schemas.user_schema import UserCreate, UserLogin, TokenResponse, UserResponse
from app.schemas.user_schema import UserUpdateRole
from app.controllers.user_controller import create_user, authenticate_user, update_user_role, get_all_users
from app.core.security import decode_token, create_access_token, get_current_user, admin_required
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate
from dotenv import load_dotenv
import os

load_dotenv()

router = APIRouter(prefix="/auth", tags=["Аутентификация"])

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, session: Session = Depends(get_session)):
    """Регистрация нового пользователя"""
    user = create_user(data, session)
    return UserResponse(id=user.id, username=user.username, role=user.role)


@router.post("/login", response_model=TokenResponse)
async def login(
        data: UserLogin,  # ИСПРАВЛЕНО: принимаем данные напрямую через Pydantic
        response: Response,
        session: Session = Depends(get_session),
):
    """Авторизация (JSON) и установка access_token в cookie."""

    # Аутентификация по username и password
    tokens = authenticate_user(data.username, data.password, session)

    # Установка access_token в HttpOnly cookie с правильными параметрами
    response.set_cookie(
        key="access_token",
        value=tokens["access_token"],
        httponly=True,  # Защита от XSS
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Время жизни в секундах
        samesite="lax",  # Для лучшей совместимости
        path="/",  # Доступность на всем сайте
        secure=False,  # Для production должно быть True (требует HTTPS)
    )

    return tokens


@router.post("/refresh", response_model=dict)
def refresh_token(refresh_token: str):
    """Обновление access токена"""
    username = decode_token(refresh_token, expected_type="refresh")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный токен"
        )

    new_access_token = create_access_token(data={"sub": username})
    return {"accessToken": new_access_token, "tokenType": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user)):
    """Получение информации о текущем пользователе"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role
    )


@router.put("/{user_id}/role", response_model=UserResponse, dependencies=[Depends(admin_required)])
def change_user_role(
        user_id: int,
        new_role: UserUpdateRole,
        session: Session = Depends(get_session),
        current_user=Depends(get_current_user)
):
    """Изменение роли пользователя (только для администратора)"""
    updated_user = update_user_role(user_id, new_role.role, session)
    return UserResponse(
        id=updated_user.id,
        username=updated_user.username,
        role=updated_user.role
    )


@router.get("/users", response_model=Page[UserResponse], dependencies=[Depends(admin_required)])
def get_all_users_paginated(session: Session = Depends(get_session)):
    return paginate(session, select(User))


@router.post("/logout")
def logout(response: Response):
    """Выход из системы - удаление cookie"""
    response.delete_cookie(
        key="access_token",
        path="/"
    )
    return {"detail": "Logged out"}