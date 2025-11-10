from sqlmodel import Session
from app.db.database import engine


def get_session():
    """Получение сессии БД"""
    with Session(engine) as session:
        yield session