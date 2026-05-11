from fastapi import APIRouter, Depends, status, Response, HTTPException
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.user import User
from app.schemas.user_schema import UserCreate, UserLogin, UserResponse, TokenResponse, UserUpdateRole
from app.core.security import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, decode_token, get_current_user, admin_required
)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, session: Session = Depends(get_session)):
    if session.exec(select(User).where(User.username == data.username)).first():
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    user = User(username=data.username, password=hash_password(data.password), role="guest")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, response: Response, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == data.username)).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверные учетные данные")

    access_token = create_access_token({"sub": user.username})
    refresh_token = create_refresh_token({"sub": user.username})

    # Установка токена в куки для тестов, которые это проверяют
    response.set_cookie(key="access_token", value=access_token, httponly=True)

    return {
        "access_token": access_token,
        "refreshToken": refresh_token,
        "tokenType": "bearer"
    }


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/refresh", response_model=TokenResponse)
def refresh(refresh_token: str, session: Session = Depends(get_session)):
    username = decode_token(refresh_token, expected_type="refresh")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невалидный refresh токен")
    return {
        "access_token": create_access_token({"sub": username}),
        "tokenType": "bearer"
    }


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"detail": "Logged out"}


@router.put("/{user_id}/role", response_model=UserResponse, dependencies=[Depends(admin_required)])
def change_role(user_id: int, data: UserUpdateRole, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    user.role = data.role
    session.add(user)
    session.commit()
    session.refresh(user)
    return user