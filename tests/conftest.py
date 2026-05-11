# tests/conftest.py
import pytest
import random
from fastapi.testclient import TestClient
from sqlmodel import Session, select, func, delete
from app.main import app
from app.db.session import get_session
from app.core.security import hash_password, create_access_token
from faker import Faker
from app.schemas.airport_schema import VALID_ICAO_PREFIXES

# ✅ Прямые импорты моделей (т.к. __init__.py не экспортирует их)
from app.models.user import User
from app.models.airport import Airport
from app.models.airline import Airline
from app.models.flight import Flight
from app.models.passenger import Passenger
from app.models.booking import Booking

fake = Faker('ru_RU')
Faker.seed(42)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    from app.db.database import init_db
    init_db()
    yield


@pytest.fixture(scope="function")
def db_session():
    from app.db.database import engine
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    # ✅ ИСПРАВЛЕНО: Очистка в строгом порядке зависимостей (сначала дети, потом родители)
    # 1. Бронирования (ссылаются на Рейсы и Пассажиров)
    session.execute(delete(Booking))
    # 2. Рейсы (ссылаются на Авиакомпании и Аэропорты)
    session.execute(delete(Flight))
    # 3. Пассажиры
    session.execute(delete(Passenger))
    # 4. Авиакомпании
    session.execute(delete(Airline))
    # 5. Аэропорты
    session.execute(delete(Airport))
    # 6. Пользователи
    session.execute(delete(User))

    session.commit()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# --- Динамические ID для негативных тестов ---
def get_max_id(session, model):
    result = session.exec(select(func.max(model.id))).first()
    return (result or 0) + 1


@pytest.fixture
def max_airport_id(db_session): return get_max_id(db_session, Airport)


@pytest.fixture
def max_flight_id(db_session): return get_max_id(db_session, Flight)


@pytest.fixture
def max_passenger_id(db_session): return get_max_id(db_session, Passenger)


@pytest.fixture
def max_booking_id(db_session): return get_max_id(db_session, Booking)


@pytest.fixture
def max_user_id(db_session): return get_max_id(db_session, User)


# --- Фикстуры данных ---
@pytest.fixture
def fake_user_data():
    return {
        "username": f"user_{fake.numerify('####')}",
        "password": fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
    }


@pytest.fixture
def fake_airline_data():
    return {"code": fake.lexify("???").upper(), "name": fake.company() + " Airlines"}


@pytest.fixture
def fake_airport_data():
    prefix = random.choice(list(VALID_ICAO_PREFIXES))
    suffix = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=4 - len(prefix)))
    return {"icaoCode": prefix + suffix, "name": fake.city() + " Intl"}


@pytest.fixture
def fake_passenger_data():
    return {
        "passportNumber": f"{fake.numerify('####')}-{fake.numerify('######')}",
        "passportIssuedBy": f"{fake.city()} UVMS",
        "passportIssueDate": "2020-01-01",
        "fullName": fake.name(),
        "birthDate": "1990-01-01"
    }


@pytest.fixture
def fake_flight_data(db_session, fake_airline_data, fake_airport_data):
    from app.schemas.airline_schema import AirlineCreate
    from app.schemas.airport_schema import AirportCreate
    from app.controllers import airline_controller, airport_controller

    airline_controller.create_airline(AirlineCreate(**fake_airline_data), db_session)
    airport_controller.create_airport(AirportCreate(**fake_airport_data), db_session)

    arr_icao = random.choice(list(VALID_ICAO_PREFIXES)) + ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=2))
    while arr_icao == fake_airport_data["icaoCode"]:
        arr_icao = random.choice(list(VALID_ICAO_PREFIXES)) + ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=2))
    airport_controller.create_airport(AirportCreate(icaoCode=arr_icao, name="Arrival"), db_session)

    return {
        "flightNumber": f"{fake_airline_data['code']}-{fake.numerify('###')}",
        "airlineCode": fake_airline_data["code"],
        "departureAirportIcao": fake_airport_data["icaoCode"],
        "arrivalAirportIcao": arr_icao,
        "departureDate": "2026-12-12", "departureTime": "10:00:00",
        "totalSeats": 150, "freeSeats": 50
    }


# --- Токены ---
@pytest.fixture
def admin_token(db_session, fake_user_data):
    u = User(username=f"admin_{fake.numerify('####')}", password=hash_password("Admin123!"), role="admin")
    db_session.add(u);
    db_session.commit()
    return create_access_token({"sub": u.username})


@pytest.fixture
def dispatcher_token(db_session, fake_user_data):
    u = User(username=f"disp_{fake.numerify('####')}", password=hash_password("Disp123!"), role="dispatcher")
    db_session.add(u);
    db_session.commit()
    return create_access_token({"sub": u.username})


@pytest.fixture
def guest_token(db_session, fake_user_data):
    u = User(username=f"guest_{fake.numerify('####')}", password=hash_password("Guest123!"), role="guest")
    db_session.add(u);
    db_session.commit()
    return create_access_token({"sub": u.username})