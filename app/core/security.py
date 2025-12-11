from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from typing import Optional

from app.db.session import get_session
from app.models.user import User

from dotenv import load_dotenv
import os

load_dotenv()

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
# ИЗМЕНЕНО: используем HTTPBearer вместо OAuth2PasswordBearer
security = HTTPBearer(auto_error=False)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
DATABASE_URL = os.getenv("DATABASE_URL")

def hash_password(password: str) -> str:
    """Хеширование пароля"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    """Создание JWT токена"""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict):
    """Создание refresh токена"""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str, expected_type: str = "access"):
    """Декодирование токена с проверкой типа"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_type = payload.get("type")
        if token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный тип токена"
            )
        return payload.get("sub")
    except JWTError:
        return None


async def get_token_from_header_or_cookie(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """
    ИСПРАВЛЕНО: Получает токен из заголовка Authorization или из куки access_token.
    Сначала проверяет заголовок, затем куки.
    """
    # Сначала пробуем получить токен из заголовка Authorization
    if credentials:
        return credentials.credentials

    # Затем пробуем получить токен из куки
    token_in_cookie = request.cookies.get("access_token")
    if token_in_cookie:
        return token_in_cookie

    # Если ни в одном месте токен не найден, выбрасываем 401
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Токен не предоставлен ни в Authorization, ни в cookie 'access_token'",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: str = Depends(get_token_from_header_or_cookie),
    session: Session = Depends(get_session)
):
    """Получение текущего пользователя по токену"""
    username = decode_token(token, expected_type="access")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный токен"
        )

    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден"
        )
    return user


def admin_required(user=Depends(get_current_user)):
    """Проверка прав администратора"""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора"
        )
    return user


def dispatcher_or_higher(user = Depends(get_current_user)):
    """Проверка, что пользователь авторизован и имеет роль dispatcher или выше (admin)."""
    if user.role == "guest":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуется роль диспетчера или выше"
        )
    return user