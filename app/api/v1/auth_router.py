# app/api/v1/auth_router.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.db.session import get_session
from app.schemas.user_schema import UserCreate, UserLogin, TokenResponse, UserResponse
from app.schemas.user_schema import UserUpdateRole # Создадим новую схему
from app.controllers.user_controller import create_user, authenticate_user, update_user_role, get_all_users
from app.core.security import decode_token, create_access_token, get_current_user, admin_required
# --- /ДОБАВЛЕНО ---

router = APIRouter(prefix="/auth", tags=["Аутентификация"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, session: Session = Depends(get_session)):
    """Регистрация нового пользователя"""
    user = create_user(data, session)
    return UserResponse(id=user.id, username=user.username, role=user.role)


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin = Depends(UserLogin.as_form), session: Session = Depends(get_session)):
    """Авторизация и получение токена"""
    return authenticate_user(data.username, data.password, session)


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
    new_role: UserUpdateRole, # Используем новую схему
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user) # Опционально, можно убрать, так как admin_required уже проверяет
):
    """Изменение роли пользователя (только для администратора)"""
    updated_user = update_user_role(user_id, new_role.role, session)
    return UserResponse(
        id=updated_user.id,
        username=updated_user.username,
        role=updated_user.role
    )

@router.get("/users", response_model=List[UserResponse], dependencies=[Depends(admin_required)])
def get_all_users_endpoint(session: Session = Depends(get_session)):
    """Получение списка всех пользователей (только для администратора)"""
    users = get_all_users(session)
    return [UserResponse(id=u.id, username=u.username, role=u.role) for u in users]
