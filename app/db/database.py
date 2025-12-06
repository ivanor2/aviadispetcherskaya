from sqlmodel import SQLModel, create_engine
from app.models.flight import Flight
from app.models.booking import Booking
from app.models.passenger import Passenger
from app.models.user import User
from app.models.airport import Airport

from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)


def init_db():
    """Инициализация базы данных"""
    SQLModel.metadata.create_all(engine)


def close_db():
    """Закрытие соединения с БД"""
    engine.dispose()


def get_engine():
    """Получение engine для миграций"""
    return engine
