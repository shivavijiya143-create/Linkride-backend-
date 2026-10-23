from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Role = Literal["passenger", "rider"]

class RegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Role = "passenger"
    phone: str | None = Field(default=None, max_length=30)

    @field_validator("full_name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be blank")
        return value

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    email: EmailStr
    role: str
    phone: str | None
    created_at: datetime

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RideCreate(BaseModel):
    pickup: str = Field(min_length=2, max_length=160)
    destination: str = Field(min_length=2, max_length=160)
    travel_date: date
    departure_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    total_seats: int = Field(ge=1, le=20)
    fare_per_seat: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    notes: str | None = Field(default=None, max_length=1000)

class RideUpdate(BaseModel):
    pickup: str | None = Field(default=None, min_length=2, max_length=160)
    destination: str | None = Field(default=None, min_length=2, max_length=160)
    travel_date: date | None = None
    departure_time: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    total_seats: int | None = Field(default=None, ge=1, le=20)
    fare_per_seat: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    notes: str | None = Field(default=None, max_length=1000)
    status: Literal["ACTIVE", "CANCELLED"] | None = None

class RideOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    rider_id: int
    pickup: str
    destination: str
    travel_date: date
    departure_time: str
    total_seats: int
    available_seats: int
    fare_per_seat: Decimal
    notes: str | None
    status: str
    created_at: datetime

class BookingCreate(BaseModel):
    ride_id: int = Field(gt=0)
    seats_requested: int = Field(ge=1, le=20)

class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ride_id: int
    passenger_id: int
    seats_requested: int
    status: str
    created_at: datetime

class BookingDecision(BaseModel):
    status: Literal["CONFIRMED", "REJECTED"]
