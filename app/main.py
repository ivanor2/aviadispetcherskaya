# app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi_pagination import add_pagination
from app.db.database import init_db, close_db

# V1
from app.api.v1 import auth_router as v1_auth, flight_router as v1_flight, passenger_router as v1_passenger
from app.api.v1 import booking_router as v1_booking, airport_router as v1_airport, airline_router as v1_airline

# V2
from app.api.v2 import auth_router as v2_auth, flight_router as v2_flight, passenger_router as v2_passenger
from app.api.v2 import booking_router as v2_booking, airport_router as v2_airport, airline_router as v2_airline

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    close_db()

# 🔥 Главное приложение — с отключёнными docs, чтобы не было каши
main_app = FastAPI(
    lifespan=lifespan,
    title="Airport Dispatcher API",
    docs_url=None,      # ❌ Отключаем /docs на корне
    redoc_url=None
)

# === Единый app для v1 + v2 ===
app = FastAPI(
    title="API v1/v2",
    version="2.0.0",
    description="v1: legacy | v2: pagination, validation, filters",
    lifespan=lifespan,
    docs_url="/docs",        # ✅ Документация будет по /docs
    openapi_url="/openapi.json"
)

# ✅ ВАЖНО: роутеры v1/v2 НЕ должны иметь собственного prefix="/auth" и т.п.
# Иначе получится /api/v1/auth/auth

# V1
app.include_router(v1_auth.router, prefix="/api/v1/auth", tags=["v1: Auth"])
app.include_router(v1_airport.router, prefix="/api/v1/airports", tags=["v1: Airports"])
app.include_router(v1_airline.router, prefix="/api/v1/airlines", tags=["v1: Airlines"])
app.include_router(v1_flight.router, prefix="/api/v1/flights", tags=["v1: Flights"])
app.include_router(v1_passenger.router, prefix="/api/v1/passengers", tags=["v1: Passengers"])
app.include_router(v1_booking.router, prefix="/api/v1/bookings", tags=["v1: Bookings"])

# V2
app.include_router(v2_auth.router, prefix="/api/v2/auth", tags=["v2: Auth"])
app.include_router(v2_airport.router, prefix="/api/v2/airports", tags=["v2: Airports"])
app.include_router(v2_airline.router, prefix="/api/v2/airlines", tags=["v2: Airlines"])
app.include_router(v2_flight.router, prefix="/api/v2/flights", tags=["v2: Flights"])
app.include_router(v2_passenger.router, prefix="/api/v2/passengers", tags=["v2: Passengers"])
app.include_router(v2_booking.router, prefix="/api/v2/bookings", tags=["v2: Bookings"])

# ✅ Обязательно добавляем пагинацию!
add_pagination(app)

# Монтируем app к main_app
main_app.mount("/", app)

@main_app.get("/")
def root():
    return {
        "message": "Airport Dispatcher API Ready",
        "docs": "/docs",  # Теперь /docs показывает ВСЕ роуты (v1 + v2)
        "note": "Используй префиксы /api/v1/... или /api/v2/... в запросах"
    }