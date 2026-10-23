from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    String, Integer, Date, DateTime, ForeignKey, Numeric, Text, CheckConstraint,
    Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="passenger", nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    rides: Mapped[list["Ride"]] = relationship(back_populates="rider")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="passenger")

class Ride(Base):
    __tablename__ = "rides"
    __table_args__ = (
        CheckConstraint("total_seats >= 1", name="ck_ride_total_seats"),
        CheckConstraint("available_seats >= 0", name="ck_ride_available_seats"),
        Index("ix_rides_route_date", "pickup", "destination", "travel_date"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    rider_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    pickup: Mapped[str] = mapped_column(String(160), nullable=False)
    destination: Mapped[str] = mapped_column(String(160), nullable=False)
    travel_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    departure_time: Mapped[str] = mapped_column(String(10), nullable=False)
    total_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    available_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    fare_per_seat: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    rider: Mapped[User] = relationship(back_populates="rides")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="ride")

class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("seats_requested >= 1", name="ck_booking_seats"),
        Index("ix_bookings_ride_status", "ride_id", "status"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ride_id: Mapped[int] = mapped_column(ForeignKey("rides.id"), nullable=False, index=True)
    passenger_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    seats_requested: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    ride: Mapped[Ride] = relationship(back_populates="bookings")
    passenger: Mapped[User] = relationship(back_populates="bookings")
