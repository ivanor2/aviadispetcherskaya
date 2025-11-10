from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.db.session import get_session
from app.schemas.user_schema import UserCreate, UserLogin, TokenResponse, UserResponse
from app.controllers.user_controller import create_user, authenticate_user
from app.core.security import decode_token, create_access_token, get_current_user

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
    username = decode_token(refresh_token)
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