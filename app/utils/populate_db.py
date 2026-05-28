import sys
import argparse
from pathlib import Path
from faker import Faker
from sqlmodel import Session, select
from app.db.database import engine
from app.models.airport import Airport
from app.models.passenger import Passenger
from app.models.flight import Flight
from app.models.booking import Booking, generate_booking_code
from app.models.airline import Airline  # ✅ НОВОЕ
from datetime import date, time, timedelta, datetime
import random
import re

# Добавляем корень проекта, чтобы импорты работали при запуске напрямую
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

fake = Faker("ru_RU")
Faker.seed(42)  # для воспроизводимости

# --- Импортируем валидные префиксы из схемы (чтобы не дублировать) ---
try:
    from app.schemas.airport_schema import VALID_ICAO_PREFIXES
except ImportError:
    VALID_ICAO_PREFIXES = {"UU", "UW", "EV", "EP", "LT", "ED", "EG", "LF", "LE", "SK", "MM", "K"}


def generate_icao_code() -> str:
    prefix = random.choice(list(VALID_ICAO_PREFIXES))
    suffix_len = 4 - len(prefix)
    suffix = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=suffix_len))
    return (prefix + suffix)[:4]


def generate_passport_number() -> str:
    series = f"{random.randint(1000, 9999)}"
    number = f"{random.randint(100000, 999999)}"
    return f"{series}-{number}"


def generate_airlines(count: int) -> list[Airline]:
    """Генерирует список авиакомпаний с уникальными 3-буквенными кодами"""
    predefined = [
        ("AFL", "Аэрофлот"), ("SVR", "Россия"), ("UTK", "ЮТэйр"),
        ("SBI", "S7 Airlines"), ("DLH", "Lufthansa"), ("BAW", "British Airways"),
        ("AFR", "Air France"), ("KLM", "KLM"), ("AAL", "American Airlines"),
        ("UAL", "United Airlines"), ("DAL", "Delta Air Lines"), ("CPA", "Cathay Pacific"),
        ("SIA", "Singapore Airlines"), ("UAE", "Emirates"), ("ETD", "Etihad Airways"),
        ("QTR", "Qatar Airways"), ("RYA", "Ryanair"), ("WZZ", "Wizz Air"),
        ("EZY", "easyJet"), ("TAP", "TAP Air Portugal"), ("LOT", "LOT Polish Airlines"),
        ("FIN", "Finnair"), ("SAS", "Scandinavian Airlines"), ("AEE", "Aegean Airlines"),
        ("IBE", "Iberia"), ("VLG", "Vueling"), ("TRA", "Transavia"), ("TUI", "TUI fly"),
        ("CCA", "Air China"), ("CES", "China Eastern"), ("CSN", "China Southern"),
        ("JAL", "Japan Airlines"), ("ANA", "ANA"), ("KAL", "Korean Air"),
        ("SVA", "Saudi Arabian"), ("MSR", "EgyptAir"), ("ETH", "Ethiopian Airlines"),
        ("KEN", "Kenya Airways"), ("SAA", "South African Airways"), ("LAM", "LAM Mozambique")
    ]

    airlines = []
    used_codes = set()
    for i in range(count):
        if i < len(predefined):
            code, name = predefined[i]
        else:
            code = fake.lexify("???").upper()
            while code in used_codes or len(code) != 3:
                code = fake.lexify("???").upper()
            name = f"{fake.company()} Airlines"
        used_codes.add(code)
        airlines.append(Airline(code=code, name=name))
    return airlines


def populate_database(
        count_airlines: int = 20,
        count_airports: int = 100,
        count_passengers: int = 100,
        count_flights: int = 100,
        count_bookings: int = 100
):
    print("🔍 Генерация тестовых данных...")
    print(f"  - Авиакомпаний: {count_airlines}")
    print(f"  - Аэропортов: {count_airports}")
    print(f"  - Пассажиров: {count_passengers}")
    print(f"  - Рейсов: {count_flights}")
    print(f"  - Бронирований: {count_bookings}")

    # === 1. Авиакомпании ===
    airlines = generate_airlines(count_airlines)
    print(f"✅ Сгенерировано {len(airlines)} авиакомпаний")

    # === 2. Аэропорты ===
    used_icao = set()
    airports = []
    for _ in range(count_airports):
        while True:
            icao = generate_icao_code()
            if icao not in used_icao:
                used_icao.add(icao)
                break
        name = fake.city() + " " + random.choice(["International", "Regional", "City", "Central"]) + " Airport"
        airports.append(Airport(icao_code=icao, name=name))
    print(f"✅ Сгенерировано {len(airports)} аэропортов")

    # === 3. Пассажиры ===
    used_passports = set()
    passengers = []
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

    # === 4. Вставка базовых сущностей в БД ===
    with Session(engine) as session:
        session.add_all(airlines)
        session.add_all(airports)
        session.add_all(passengers)
        session.commit()

        for a in airlines: session.refresh(a)
        for a in airports: session.refresh(a)
        for p in passengers: session.refresh(p)

        # === 5. Рейсы ===
        used_flight_numbers = set()
        base_date = date.today()
        flights = []

        for _ in range(count_flights):
            airline = random.choice(airlines)

            # ✅ Генерируем номер рейса строго с кодом выбранной авиакомпании
            while True:
                flight_num = f"{airline.code}-{random.randint(100, 999)}"
                if flight_num not in used_flight_numbers:
                    used_flight_numbers.add(flight_num)
                    break

            dep_airport = random.choice(airports)
            # Исключаем рейсы "туда-сюда" в один аэропорт
            eligible_arr = [a for a in airports if a.icao_code != dep_airport.icao_code]
            arr_airport = random.choice(eligible_arr) if eligible_arr else dep_airport

            total_seats = random.choice([120, 150, 180, 200, 220, 250])
            # ✅ free_seets всегда равно total_seats при создании рейса
            free_seats = total_seats
            
            # Цены для рейса
            base_price = round(random.uniform(5000, 50000), 2)  # Базовая цена от 5000 до 50000
            baggage_price = round(random.uniform(500, 5000), 2)  # Цена багажа от 500 до 5000

            # Генерируем время отправления и прибытия
            dep_time = time(random.randint(0, 23), random.choice([0, 15, 30, 45]))
            
            # Генерируем время прибытия (департура + случайное время полета от 1 до 12 часов)
            flight_duration_hours = random.randint(1, 12)
            flight_duration_minutes = random.choice([0, 15, 30, 45])
            arrival_hour = (dep_time.hour + flight_duration_hours) % 24
            arrival_minute = (dep_time.minute + flight_duration_minutes) % 60
            if dep_time.minute + flight_duration_minutes >= 60:
                arrival_hour = (arrival_hour + 1) % 24
            arrival_t = time(arrival_hour, arrival_minute)

            flights.append(Flight(
                flight_number=flight_num,
                airline_code=airline.code,  # ✅ FK к Airline.code
                departure_airport_icao=dep_airport.icao_code,  # ✅ FK к Airport.icao_code (ИСПРАВЛЕНО)
                arrival_airport_icao=arr_airport.icao_code,  # ✅ FK к Airport.icao_code (ИСПРАВЛЕНО)
                departure_date=base_date + timedelta(days=random.randint(1, 30)),
                departure_time=dep_time,
                arrival_time=arrival_t,
                total_seats=total_seats,
                free_seats=free_seats,
                base_price=base_price,
                baggage_price=baggage_price
            ))

        session.add_all(flights)
        session.commit()
        for f in flights: session.refresh(f)
        print(f"✅ Сгенерировано {len(flights)} рейсов")

        # === 6. Бронирования ===
        used_codes = set()
        bookings = []

        # Ограничиваем кол-во бронирований реальным количеством свободных мест
        total_free_seats = sum(f.free_seats for f in flights)
        target_bookings = min(count_bookings, total_free_seats)
        
        # Варианты для генерации данных
        payment_types = ["card", "cash", "online"]
        
        for _ in range(target_bookings):
            eligible_flights = [f for f in flights if f.free_seats > 0]
            if not eligible_flights:
                print("⚠️ Нет рейсов с доступными местами. Генерация бронирований завершена.")
                break

            flight = random.choice(eligible_flights)
            passenger = random.choice(passengers)

            # Проверяем, не бронировал ли этот пассажир уже этот рейс
            existing = session.exec(
                select(Booking).where(
                    Booking.flight_id == flight.id,
                    Booking.passenger_id == passenger.id
                )
            ).first()
            if existing:
                continue

            code = generate_booking_code()
            while code in used_codes:
                code = generate_booking_code()
            used_codes.add(code)
            
            # Генерируем случайные значения для новых полей
            baggage = random.choice([True, False])
            payment = random.choice(payment_types)
            additional_fees = round(random.uniform(0, 5000), 2)  # Доп сборы от 0 до 5000
            class_type = random.choice(["economy", "business", "first"])
            
            # Генерируем номер места
            row = random.randint(1, flight.total_seats // 6 + 1)
            seat_letter = random.choice(['A', 'B', 'C', 'D', 'E', 'F'])
            seat_num = f"{row}{seat_letter}"

            bookings.append(Booking(
                booking_code=code,
                flight_id=flight.id,
                passenger_id=passenger.id,
                seat=seat_num,
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 7)),
                baggage_allowed=baggage,
                payment_type=payment,
                additional_fees=additional_fees,
                class_type=class_type
            ))
            flight.free_seats -= 1
            session.add(flight)

        session.add_all(bookings)
        session.commit()
        print(f"✅ Сгенерировано {len(bookings)} бронирований")

    print("🎉 База данных успешно заполнена тестовыми данными!")


def main():
    parser = argparse.ArgumentParser(description='Заполнение базы данных тестовыми данными.')
    parser.add_argument('--airlines', type=int, default=20, help='Количество авиакомпаний (по умолчанию: 20)')
    parser.add_argument('--airports', type=int, default=100, help='Количество аэропортов (по умолчанию: 100)')
    parser.add_argument('--passengers', type=int, default=100, help='Количество пассажиров (по умолчанию: 100)')
    parser.add_argument('--flights', type=int, default=100, help='Количество рейсов (по умолчанию: 100)')
    parser.add_argument('--bookings', type=int, default=100, help='Количество бронирований (по умолчанию: 100)')
    args = parser.parse_args()

    populate_database(
        count_airlines=args.airlines,
        count_airports=args.airports,
        count_passengers=args.passengers,
        count_flights=args.flights,
        count_bookings=args.bookings
    )


if __name__ == "__main__":
    main()