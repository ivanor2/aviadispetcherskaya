# app/utils/populate_db.py
import sys
import argparse
from pathlib import Path
from faker import Faker
from sqlmodel import Session
from app.db.database import engine
from app.models.airport import Airport
from app.models.passenger import Passenger
from app.models.flight import Flight
from app.models.booking import Booking, generate_booking_code
from datetime import date, time, timedelta, datetime
import random
import re

# Добавляем корень проекта, чтобы импорты работали при запуске напрямую
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

fake = Faker("ru_RU")
Faker.seed(42)  # для воспроизводимости


def generate_icao_code(valid_prefixes) -> str:
    prefix = random.choice(list(valid_prefixes))
    suffix_len = 4 - len(prefix)
    suffix = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=suffix_len))
    return (prefix + suffix)[:4]


def generate_flight_number() -> str:
    airline = fake.lexify("??", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    if random.random() < 0.3:
        airline += fake.lexify("?", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    number = f"{random.randint(100, 999)}"
    return f"{airline}-{number}"


def generate_passport_number() -> str:
    series = f"{random.randint(1000, 9999)}"
    number = f"{random.randint(100000, 999999)}"
    return f"{series}-{number}"


def populate_database(count_airports=100, count_passengers=100, count_flights=100, count_bookings=100):
    print("🔍 Генерация тестовых данных... ")
    print(f"  - Аэропортов: {count_airports}")
    print(f"  - Пассажиров: {count_passengers}")
    print(f"  - Рейсов: {count_flights}")
    print(f"  - Бронирований: {count_bookings}")

    # Импортируем валидные префиксы из схемы (чтобы не дублировать)
    try:
        from app.schemas.airport_schema import VALID_ICAO_PREFIXES
    except ImportError:
        # Резервный вариант — минимальный набор
        VALID_ICAO_PREFIXES = {"UU", "UW", "EV", "EP", "LT", "ED", "EG", "LF", "LE", "SK", "MM", "K"}

    airports = []
    passengers = []
    flights = []
    bookings = []

    # === 1. Аэропорты ===
    used_icao = set()
    for _ in range(count_airports):
        while True:
            icao = generate_icao_code(VALID_ICAO_PREFIXES)
            if icao not in used_icao:
                used_icao.add(icao)
                break
        name = fake.city() + " " + random.choice(["International", "Regional", "City", "Central"]) + " Airport"
        airports.append(Airport(icao_code=icao, name=name))
    print(f"✅ Сгенерировано {len(airports)} аэропортов")

    # === 2. Пассажиры ===
    used_passports = set()
    for _ in range(count_passengers):
        while True:
            passport = generate_passport_number()
            if passport not in used_passports:
                used_passports.add(passport)
                break
        passengers.append(Passenger(
            passport_number=passport,
            passport_issued_by=fake.city() + " УФМС",
            passport_issue_date=fake.date_between(start_date="-10y", end_date="-1y"),
            full_name=fake.name(),
            birth_date=fake.date_between(start_date="-70y", end_date="-18y")
        ))
    print(f"✅ Сгенерировано {len(passengers)} пассажиров")

    # === 3. Вставка в БД и получение ID ===
    with Session(engine) as session:
        # Аэропорты
        session.add_all(airports)
        session.commit()
        for a in airports:
            session.refresh(a)

        # Пассажиры
        session.add_all(passengers)
        session.commit()
        for p in passengers:
            session.refresh(p)

        # === 4. Рейсы ===
        used_flight_numbers = set()
        base_date = date.today()
        for _ in range(count_flights):
            while True:
                fn = generate_flight_number()
                if fn not in used_flight_numbers:
                    used_flight_numbers.add(fn)
                    break

            dep_airport = random.choice(airports)
            arr_airport = random.choice([a for a in airports if a.id != dep_airport.id])
            total_seats = random.choice([120, 150, 180, 200, 220, 250])
            free_seats = random.randint(0, total_seats)

            flights.append(Flight(
                flight_number=fn,
                airline_name=fake.company() + " Airlines",
                departure_airport_id=dep_airport.id,
                arrival_airport_id=arr_airport.id,
                departure_date=base_date + timedelta(days=random.randint(1, 30)),
                departure_time=time(random.randint(0, 23), random.choice([0, 15, 30, 45])),
                total_seats=total_seats,
                free_seats=free_seats
            ))

        session.add_all(flights)
        session.commit()
        for f in flights:
            session.refresh(f)

        print(f"✅ Сгенерировано {len(flights)} рейсов")

        # === 5. Бронирования ===
        used_codes = set()
        for _ in range(min(count_bookings, len(flights) * max([f.total_seats for f in flights]))): # Ограничение по возможному количеству
            eligible_flights = [f for f in flights if f.free_seats > 0]
            if not eligible_flights:
                 print("⚠️ Нет рейсов с доступными местами для генерации дополнительных бронирований.")
                 break
            flight = random.choice(eligible_flights)
            passenger = random.choice(passengers)

            code = generate_booking_code()
            while code in used_codes:
                code = generate_booking_code()
            used_codes.add(code)

            bookings.append(Booking(
                booking_code=code,
                flight_id=flight.id,
                passenger_id=passenger.id,
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 7))
            ))
            flight.free_seats -= 1
            session.add(flight)

        session.add_all(bookings)
        session.commit()
        print(f"✅ Сгенерировано {len(bookings)} бронирований")

    print("🎉 База данных успешно заполнена тестовыми данными!")


def main():
    parser = argparse.ArgumentParser(description='Заполнение базы данных тестовыми данными.')
    parser.add_argument('--airports', type=int, default=100, help='Количество аэропортов для генерации (по умолчанию: 100)')
    parser.add_argument('--passengers', type=int, default=100, help='Количество пассажиров для генерации (по умолчанию: 100)')
    parser.add_argument('--flights', type=int, default=100, help='Количество рейсов для генерации (по умолчанию: 100)')
    parser.add_argument('--bookings', type=int, default=100, help='Количество бронирований для генерации (по умолчанию: 100)')

    args = parser.parse_args()

    populate_database(
        count_airports=args.airports,
        count_passengers=args.passengers,
        count_flights=args.flights,
        count_bookings=args.bookings
    )


if __name__ == "__main__":
    main()