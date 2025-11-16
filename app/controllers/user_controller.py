from sqlmodel import Session, select
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user_schema import UserCreate
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from typing import List


def create_user(data: UserCreate, session: Session) -> User:
    """Создание пользователя"""
    existing_user = session.exec(select(User).where(User.username == data.username)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем уже существует"
        )

    user = User(
        username=data.username,
        password=hash_password(data.password),
        role=data.role
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def authenticate_user(username: str, password: str, session: Session):
    """Аутентификация пользователя"""
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль"
        )

    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    # app/controllers/user_controller.py (или где находится return)

    return {
        # ИСПРАВЛЕНИЕ: Ключ должен быть "access_token" (все маленькие буквы)
        "access_token": access_token,
        "refreshToken": refresh_token,
        "tokenType": "bearer"
    }




def get_all_users(session: Session) -> List[User]:
    """Получение всех пользователей"""
    return session.exec(select(User)).all()