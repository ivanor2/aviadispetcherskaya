import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.main import app_v1
from app.db.session import get_session
from app.models.user import User
from app.db.database import engine
from faker import Faker

fake = Faker()


@pytest.fixture(scope="function")
def session():
    """
    Создает одну базу данных для тестовой функции,
    оборачивает все в транзакцию, которая откатывается в конце.
    """
    connection = engine.connect()
    transaction = connection.begin()

    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(session):
    """
    TestClient, который использует ОБЩИЙ фикстуру session.
    """

    def override_get_session():
        yield session

    app_v1.dependency_overrides[get_session] = override_get_session

    with TestClient(app_v1) as c:
        yield c

    app_v1.dependency_overrides.clear()


# --- Data Fixtures ---
@pytest.fixture
def admin_user_data():
    suffix = fake.numerify("####")
    return {"username": f"admin_test_{suffix}", "password": "StrongP@ssw0rd!"}


@pytest.fixture
def regular_user_data():
    suffix = fake.numerify("####")
    return {"username": f"user_test_{suffix}", "password": "RegularP@ssw0rd!"}


@pytest.fixture
def sample_airport_data():
    # Используем валидный префикс "UK" и алфавитный суффикс
    icao = "UK" + fake.lexify("??", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    return {"icaoCode": icao, "name": fake.city() + " Test Airport"}


@pytest.fixture
def sample_passenger_data():
    return {
        "passportNumber": fake.numerify("####-######"),
        "passportIssuedBy": fake.city() + " УФМС",
        "passportIssueDate": fake.date_between(start_date="-10y", end_date="-1y").isoformat(),
        "fullName": fake.name(),
        "birthDate": fake.date_of_birth(minimum_age=18, maximum_age=90).isoformat(),
    }


@pytest.fixture
def sample_flight_data():
    return {
        "flightNumber": fake.lexify("??", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ") + "-" + fake.numerify("###"),
        "airlineName": fake.company() + " Airlines",
        "departureDate": fake.date_between(start_date="today", end_date="+30d").isoformat(),
        "departureTime": "12:00:00",
        "totalSeats": 150,
        "freeSeats": 150,
        # departureAirportId / arrivalAirportId are filled in the test
    }


# --- Auth Helpers ---
def register_and_login_user(client, username: str, password: str, role: str = "guest") -> str:
    """Регистрирует пользователя и возвращает access_token, используя общую сессию."""
    # 1. Регистрация
    reg = client.post("/auth/register", json={"username": username, "password": password})
    assert reg.status_code == 201, f"Reg failed: {reg.text}"
    user_id = reg.json()["id"]

    # 2. Повышение роли, если нужно
    if role != "guest":
        session_gen = client.app.dependency_overrides[get_session]()
        session = next(session_gen)

        user = session.get(User, user_id)
        assert user, "User not found after register"
        user.role = role
        session.add(user)
        session.commit()
        session.refresh(user)

    # 3. Логин
    login = client.post("/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200, f"Login failed: {login.text}"
    return login.json()["access_token"]


@pytest.fixture
def admin_headers(client, admin_user_data):
    token = register_and_login_user(
        client,
        admin_user_data["username"],
        admin_user_data["password"],
        role="admin"
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def regular_user_headers(client, regular_user_data):
    token = register_and_login_user(
        client,
        regular_user_data["username"],
        regular_user_data["password"],
        role="guest"
    )
    return {"Authorization": f"Bearer {token}"}