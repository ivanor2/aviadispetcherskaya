# app/schemas/airport_schema.py

from pydantic import BaseModel, Field, field_validator
from typing import Optional

# --- НОВОЕ: Множество допустимых префиксов из ТЗ ---
VALID_ICAO_PREFIXES = {
    "AG", "AN", "AY", "BG", "BI", "C", "DA", "DB", "DF", "DG", "DI", "DN", "DR", "DT", "DX",
    "EB", "ED", "EE", "EF", "EG", "EH", "EI", "EK", "EL", "EN", "EP", "ES", "ET", "EV", "EY",
    "FA", "FB", "FC", "FD", "FE", "FG", "FH", "FI", "FJ", "FK", "FL", "FM", "FN", "FO", "FP",
    "FQ", "FS", "FT", "FV", "FW", "FX", "FY", "FZ", "GA", "GB", "GC", "GE", "GF", "GG", "GL",
    "GM", "GO", "GQ", "GS", "GU", "GV", "HA", "HB", "HC", "HD", "HE", "HF", "HH", "HK", "HL",
    "HR", "HS", "HT", "HU", "K", "LA", "LB", "LC", "LD", "LE", "LF", "LG", "LH", "LI", "LJ",
    "LK", "LL", "LM", "LN", "LO", "LP", "LQ", "LR", "LS", "LT", "LU", "LV", "LW", "LX", "LY",
    "LZ", "MB", "MD", "MG", "MH", "MK", "MM", "MN", "MP", "MR", "MS", "MT", "MU", "MW", "MY",
    "MZ", "NC", "NF", "NG", "NI", "NL", "NS", "NT", "NV", "NW", "NZ", "OA", "OB", "OE", "OI",
    "OJ", "OK", "OL", "OM", "OO", "OP", "OR", "OS", "OT", "OY", "PA", "PB", "PC", "PF", "PG",
    "PH", "PJ", "PK", "PL", "PM", "PO", "PP", "PT", "PW", "RC", "RJ", "RK", "RO", "RP", "SA",
    "SB", "SC", "SD", "SE", "SF", "SG", "SK", "SL", "SM", "SN", "SO", "SP", "SS", "SU", "SV",
    "SW", "SY", "TA", "TB", "TD", "TF", "TG", "TI", "TJ", "TK", "TL", "TN", "TQ", "TR", "TT",
    "TU", "TV", "TX", "U", "UA", "UB", "UC", "UD", "UG", "UK", "UM", "UT", "VA", "VC", "VD",
    "VE", "VG", "VH", "VI", "VL", "VM", "VN", "VO", "VQ", "VR", "VT", "VV", "VY", "WA", "WB",
    "WI", "WM", "WP", "WQ", "WR", "WS", "Y", "Z", "ZK", "ZM"
}
# --- /НОВОЕ ---

class AirportCreate(BaseModel):
    icaoCode: str = Field(..., description="Официальный ICAO-код аэропорта (2-4 символа)", examples=["UUSS"])
    name: str = Field(..., max_length=200, description="Название аэропорта или страны")

    @field_validator('icaoCode')
    def validate_icao_code(cls, v):
        # Проверка длины
        if len(v) < 2 or len(v) > 4:
            raise ValueError('ICAO-код должен состоять из 2-4 символов')

        # Проверка, что код состоит только из заглавных латинских букв
        if not v.isalpha() or not v.isupper():
            raise ValueError('ICAO-код должен состоять только из заглавных латинских букв')

        # Проверка, что первые 2 символа находятся в списке допустимых префиксов
        if v[:2] not in VALID_ICAO_PREFIXES:
             raise ValueError(f'ICAO-код должен начинаться с одного из допустимых префиксов: {sorted(VALID_ICAO_PREFIXES)}')

        return v

class AirportUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200, description="Новое название аэропорта или страны")

class AirportResponse(BaseModel):
    id: int
    icaoCode: str = Field(alias="icao_code")
    name: str

    class Config:
        from_attributes = True