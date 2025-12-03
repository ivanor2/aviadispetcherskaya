from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "8a7c1f9e0b4d6f2a1c5e8f7a9b3c4d6e0f2a1c5e8f7a9b3c4d6e0f2a1c5e8f7a")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:12345@localhost:5433/airport_db")
