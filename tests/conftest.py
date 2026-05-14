# tests/conftest.py
"""
Конфигурационный файл pytest для тестов API.

Содержит фикстуры для:
- Инициализации базы данных
- Создания сессии БД с очисткой между тестами
- HTTP клиента для тестирования API
- Генерации тестовых данных (пользователи, авиакомпании, аэропорты, рейсы, пассажиры)
- Создания токенов авторизации для разных ролей
"""
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
    """
    Инициализирует базу данных перед запуском всех тестов.
    
    Фикстура выполняется один раз за сессию тестирования и автоматически
    инициализирует схему БД.
    
    Yields:
        None: После инициализации передаёт управление тестам.
    """
    from app.db.database import init_db
    init_db()
    yield


@pytest.fixture(scope="function")
def db_session():
    """
    Создаёт изолированную сессию базы данных для каждого теста.
    
    Фикстура создаёт новую транзакцию для каждого теста, очищает все таблицы
    в правильном порядке зависимостей (сначала дочерние, потом родительские),
    и откатывает изменения после завершения теста.
    
    Порядок очистки таблиц:
    1. Бронирования (Booking) - ссылаются на Рейсы и Пассажиров
    2. Рейсы (Flight) - ссылаются на Авиакомпании и Аэропорты
    3. Пассажиры (Passenger)
    4. Авиакомпании (Airline)
    5. Аэропорты (Airport)
    6. Пользователи (User)
    
    Yields:
        Session: Сессия SQLModel для взаимодействия с БД.
    """
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
    """
    Создаёт тестовый HTTP клиент для запросов к API.
    
    Переопределяет зависимость get_session для использования тестовой сессии БД,
    что обеспечивает изоляцию тестов от основной базы данных.
    
    Args:
        db_session: Фикстура сессии базы данных.
        
    Yields:
        TestClient: Клиент для отправки HTTP запросов к FastAPI приложению.
    """
    def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# --- Динамические ID для негативных тестов ---
def get_max_id(session, model):
    """
    Получает следующий доступный ID для модели.
    
    Используется в негативных тестах для проверки поведения при работе
    с несуществующими записями (например, поиск по ID, которого нет в БД).
    
    Args:
        session: Сессия базы данных.
        model: Класс модели SQLModel.
        
    Returns:
        int: Следующий доступный ID (максимальный существующий + 1).
    """
    result = session.exec(select(func.max(model.id))).first()
    return (result or 0) + 1


@pytest.fixture
def max_airport_id(db_session): 
    """Возвращает следующий доступный ID для аэропорта (для негативных тестов)."""
    return get_max_id(db_session, Airport)


@pytest.fixture
def max_flight_id(db_session): 
    """Возвращает следующий доступный ID для рейса (для негативных тестов)."""
    return get_max_id(db_session, Flight)


@pytest.fixture
def max_passenger_id(db_session): 
    """Возвращает следующий доступный ID для пассажира (для негативных тестов)."""
    return get_max_id(db_session, Passenger)


@pytest.fixture
def max_booking_id(db_session): 
    """Возвращает следующий доступный ID для бронирования (для негативных тестов)."""
    return get_max_id(db_session, Booking)


@pytest.fixture
def max_user_id(db_session): 
    """Возвращает следующий доступный ID для пользователя (для негативных тестов)."""
    return get_max_id(db_session, User)


# --- Фикстуры данных ---
@pytest.fixture
def fake_user_data():
    """
    Генерирует случайные данные пользователя для тестов.
    
    Returns:
        dict: Словарь с полями username и password.
            - username: Уникальное имя пользователя с числовым суффиксом.
            - password: Сложный пароль длиной 12 символов.
    """
    return {
        "username": f"user_{fake.numerify('####')}",
        "password": fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
    }


@pytest.fixture
def fake_airline_data():
    """
    Генерирует случайные данные авиакомпании для тестов.
    
    Returns:
        dict: Словарь с полями code и name.
            - code: Трёхбуквенный код авиакомпании (верхний регистр).
            - name: Название авиакомпании с суффиксом "Airlines".
    """
    return {"code": fake.lexify("???").upper(), "name": fake.company() + " Airlines"}


@pytest.fixture
def fake_airport_data():
    """
    Генерирует случайные данные аэропорта с валидным ICAO-кодом для тестов.
    
    ICAO-код формируется из префикса региона (из VALID_ICAO_PREFIXES) 
    и случайных букв до общей длины 4 символа.
    
    Returns:
        dict: Словарь с полями icaoCode и name.
            - icaoCode: Валидный 4-буквенный ICAO-код.
            - name: Название аэропорта с суффиксом "Intl".
    """
    prefix = random.choice(list(VALID_ICAO_PREFIXES))
    suffix = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=4 - len(prefix)))
    return {"icaoCode": prefix + suffix, "name": fake.city() + " Intl"}


@pytest.fixture
def fake_passenger_data():
    """
    Генерирует случайные данные пассажира для тестов.
    
    Returns:
        dict: Словарь с полями:
            - passportNumber: Номер паспорта в формате "####-######".
            - passportIssuedBy: Орган выдачи паспорта.
            - passportIssueDate: Дата выдачи (фиксированная).
            - fullName: ФИО пассажира.
            - birthDate: Дата рождения (фиксированная).
    """
    return {
        "passportNumber": f"{fake.numerify('####')}-{fake.numerify('######')}",
        "passportIssuedBy": f"{fake.city()} UVMS",
        "passportIssueDate": "2020-01-01",
        "fullName": fake.name(),
        "birthDate": "1990-01-01"
    }


@pytest.fixture
def fake_flight_data(db_session, fake_airline_data, fake_airport_data):
    """
    Генерирует случайные данные рейса и создаёт необходимые зависимости.
    
    Перед генерацией данных рейса создаёт:
    - Авиакомпанию (по данным из fake_airline_data)
    - Аэропорт вылета (по данным из fake_airport_data)
    - Аэропорт прилёта (случайный, отличный от аэропорта вылета)
    
    Args:
        db_session: Сессия базы данных.
        fake_airline_data: Данные авиакомпании.
        fake_airport_data: Данные аэропорта вылета.
        
    Returns:
        dict: Словарь с полями рейса:
            - flightNumber: Номер рейса в формате "CODE-###".
            - airlineCode: Код авиакомпании.
            - departureAirportIcao: ICAO-код аэропорта вылета.
            - arrivalAirportIcao: ICAO-код аэропорта прилёта.
            - departureDate: Дата вылета.
            - departureTime: Время вылета.
            - totalSeats: Общее количество мест.
            - freeSeats: Количество свободных мест.
    """
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
    """
    Создаёт токен доступа для пользователя с ролью admin.
    
    Создаёт нового пользователя в БД с ролью "admin" и генерирует
    JWT токен доступа для него.
    
    Args:
        db_session: Сессия базы данных.
        fake_user_data: Данные пользователя (используется только для генерации имени).
        
    Returns:
        str: JWT токен доступа для администратора.
    """
    u = User(username=f"admin_{fake.numerify('####')}", password=hash_password("Admin123!"), role="admin")
    db_session.add(u);
    db_session.commit()
    return create_access_token({"sub": u.username})


@pytest.fixture
def dispatcher_token(db_session, fake_user_data):
    """
    Создаёт токен доступа для пользователя с ролью dispatcher.
    
    Создаёт нового пользователя в БД с ролью "dispatcher" и генерирует
    JWT токен доступа для него.
    
    Args:
        db_session: Сессия базы данных.
        fake_user_data: Данные пользователя (используется только для генерации имени).
        
    Returns:
        str: JWT токен доступа для диспетчера.
    """
    u = User(username=f"disp_{fake.numerify('####')}", password=hash_password("Disp123!"), role="dispatcher")
    db_session.add(u);
    db_session.commit()
    return create_access_token({"sub": u.username})


@pytest.fixture
def guest_token(db_session, fake_user_data):
    """
    Создаёт токен доступа для пользователя с ролью guest.
    
    Создаёт нового пользователя в БД с ролью "guest" и генерирует
    JWT токен доступа для него.
    
    Args:
        db_session: Сессия базы данных.
        fake_user_data: Данные пользователя (используется только для генерации имени).
        
    Returns:
        str: JWT токен доступа для гостя.
    """
    u = User(username=f"guest_{fake.numerify('####')}", password=hash_password("Guest123!"), role="guest")
    db_session.add(u);
    db_session.commit()
    return create_access_token({"sub": u.username})