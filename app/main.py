from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.db.database import init_db, close_db
from app.api.v1 import auth_router, flight_router, passenger_router, booking_router, airport_router
from fastapi_pagination import add_pagination


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    init_db()
    yield
    close_db()


# Основное приложение
main_app = FastAPI(lifespan=lifespan)

# API v1
app_v1 = FastAPI(
    title="Airport Dispatcher API v1",
    version="1.0.0",
    description="REST API для АРМ диспетчера аэропорта",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Подключение роутеров
app_v1.include_router(airport_router.router)
app_v1.include_router(auth_router.router)
app_v1.include_router(flight_router.router)
app_v1.include_router(passenger_router.router)
app_v1.include_router(booking_router.router)

# Подключение пагинации
add_pagination(app_v1)

# Монтирование v1 к основному приложению
main_app.mount("/api/v1", app_v1)


@main_app.get("/")
def root():
    """Корневой endpoint"""
    return {
        "message": "Airport Dispatcher API",
        "version": "1.0.0",
        "docs": "/api/v1/docs",
        "redoc": "/api/v1/redoc"
    }