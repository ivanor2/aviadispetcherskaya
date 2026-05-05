# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, select
from app.db.database import engine, init_db
from app.db.session import get_session
from app.main import app
from app.models.user import User
from app.core.security import hash_password, create_access_token
from faker import Faker

fake = Faker()


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Инициализация БД перед всеми тестами"""
    init_db()
    yield
    # Очистка после тестов (опционально)
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session():
    """Фикстура сессии БД с откатом транзакции после теста"""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """TestClient с переопределённой зависимостью get_session"""

    def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def admin_token(db_session):
    """Токен администратора - ИСПРАВЛЕНО: сохраняем username ДО закрытия сессии"""
    username = f"test_admin_{fake.numerify('####')}"
    password = hash_password("Admin123!")

    user = User(username=username, password=password, role="admin")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)  # Гарантируем, что все атрибуты загружены

    # ✅ КЛЮЧЕВОЕ: сохраняем username в строку ДО выхода из сессии
    token = create_access_token({"sub": user.username})
    return token


@pytest.fixture
def guest_token(db_session):
    """Токен гостя - ИСПРАВЛЕНО"""
    username = f"test_guest_{fake.numerify('####')}"
    password = hash_password("Guest123!")

    user = User(username=username, password=password, role="guest")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": user.username})
    return token


@pytest.fixture
def dispatcher_token(db_session):
    """Токен диспетчера"""
    username = f"test_dispatch_{fake.numerify('####')}"
    password = hash_password("Dispatch123!")

    user = User(username=username, password=password, role="dispatcher")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": user.username})
    return token