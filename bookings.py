from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Booking, Ride, User
from app.schemas import BookingCreate, BookingOut, BookingDecision
from app.security import get_current_user, require_role

router = APIRouter(prefix="/api", tags=["Bookings"])

@router.post("/bookings", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def request_booking(
    payload: BookingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("passenger")),
):
    ride = db.get(Ride, payload.ride_id)
    if not ride or ride.status != "ACTIVE":
        raise HTTPException(status_code=404, detail="Active ride not found")
    if ride.rider_id == user.id:
        raise HTTPException(status_code=400, detail="You cannot book your own ride")
    if ride.travel_date < __import__("datetime").date.today():
        raise HTTPException(status_code=400, detail="This ride has already departed")
    existing = db.scalar(select(Booking).where(
        Booking.ride_id == ride.id,
        Booking.passenger_id == user.id,
        Booking.status.in_(["PENDING", "CONFIRMED"]),
    ))
    if existing:
        raise HTTPException(status_code=409, detail="You already have an active booking for this ride")
    if payload.seats_requested > ride.available_seats:
        raise HTTPException(status_code=409, detail="Not enough seats available")
    booking = Booking(
        ride_id=ride.id,
        passenger_id=user.id,
        seats_requested=payload.seats_requested,
        status="PENDING",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking

@router.get("/bookings/my", response_model=list[BookingOut])
def my_bookings(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return list(db.scalars(select(Booking).where(
        Booking.passenger_id == user.id
    ).order_by(Booking.created_at.desc())).all())

@router.patch("/bookings/{booking_id}", response_model=BookingOut)
def decide_booking(
    booking_id: int,
    payload: BookingDecision,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("rider")),
):
    booking = db.scalar(select(Booking).where(Booking.id == booking_id))
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    # Lock ride row to serialize seat allocation updates in MySQL.
    ride = db.scalar(select(Ride).where(Ride.id == booking.ride_id).with_for_update())
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    if ride.rider_id != user.id:
        raise HTTPException(status_code=403, detail="Only the ride owner can decide this booking")
    if booking.status != "PENDING":
        raise HTTPException(status_code=409, detail="Only pending bookings can be decided")
    if payload.status == "CONFIRMED":
        if ride.status != "ACTIVE" or ride.available_seats < booking.seats_requested:
            raise HTTPException(status_code=409, detail="Not enough seats available or ride is inactive")
        ride.available_seats -= booking.seats_requested
    booking.status = payload.status
    db.commit()
    db.refresh(booking)
    return booking

@router.post("/bookings/{booking_id}/cancel", response_model=BookingOut)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    booking = db.scalar(select(Booking).where(Booking.id == booking_id))
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    ride = db.scalar(select(Ride).where(Ride.id == booking.ride_id).with_for_update())
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    if booking.passenger_id != user.id and ride.rider_id != user.id:
        raise HTTPException(status_code=403, detail="You cannot cancel this booking")
    if booking.status not in ("PENDING", "CONFIRMED"):
        raise HTTPException(status_code=409, detail="This booking cannot be cancelled")
    if booking.status == "CONFIRMED":
        ride.available_seats = min(ride.total_seats, ride.available_seats + booking.seats_requested)
    booking.status = "CANCELLED"
    db.commit()
    db.refresh(booking)
    return booking
