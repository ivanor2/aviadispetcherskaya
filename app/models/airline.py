from sqlmodel import SQLModel, Field

class Airline(SQLModel, table=True):
    __tablename__ = "airline"
    code: str = Field(primary_key=True, max_length=3, index=True, description="3-буквенный IATA/ICAO код")
    name: str = Field(max_length=100, description="Название авиакомпании")