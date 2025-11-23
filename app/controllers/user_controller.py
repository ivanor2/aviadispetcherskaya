# app/controllers/user_controller.py
from sqlmodel import Session, select
from fastapi import HTTPException, status # Убедитесь, что импортированы
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
        role="dispatcher"
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

    return {
        "access_token": access_token,
        "refreshToken": refresh_token,
        "tokenType": "bearer"
    }


def get_all_users(session: Session) -> List[User]:
    """Получение всех пользователей"""
    return session.exec(select(User)).all()

# --- НОВАЯ ФУНКЦИЯ ---
def update_user_role(user_id: int, new_role: str, session: Session) -> User:
    """Обновление роли пользователя (только для администратора)"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    # Проверка, что новая роль допустима (например, "dispatcher", "admin")
    # Можно добавить список разрешённых ролей
    allowed_roles = ["dispatcher", "admin"] # Пример списка
    if new_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимая роль. Допустимые значения: {allowed_roles}"
        )

    user.role = new_role
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def get_all_users(session: Session) -> List[User]:
    """Получение всех пользователей"""
    return session.exec(select(User)).all()