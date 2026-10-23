from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Ride, User, Booking
from app.schemas import RideCreate, RideUpdate, RideOut, BookingOut
from app.security import get_current_user, require_role

router = APIRouter(prefix="/api/rides", tags=["Rides"])

@router.post("", response_model=RideOut, status_code=status.HTTP_201_CREATED)
def create_ride(
    payload: RideCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("rider")),
):
    if payload.travel_date < date.today():
        raise HTTPException(status_code=422, detail="Travel date cannot be in the past")
    ride = Ride(
        rider_id=user.id,
        pickup=payload.pickup.strip(),
        destination=payload.destination.strip(),
        travel_date=payload.travel_date,
        departure_time=payload.departure_time,
        total_seats=payload.total_seats,
        available_seats=payload.total_seats,
        fare_per_seat=payload.fare_per_seat,
        notes=payload.notes,
    )
    db.add(ride)
    db.commit()
    db.refresh(ride)
    return ride

@router.get("", response_model=list[RideOut])
def search_rides(
    pickup: str | None = Query(default=None, max_length=160),
    destination: str | None = Query(default=None, max_length=160),
    travel_date: date | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(Ride).where(Ride.status == "ACTIVE", Ride.available_seats > 0)
    if pickup:
        stmt = stmt.where(Ride.pickup.ilike(f"%{pickup.strip()}%"))
    if destination:
        stmt = stmt.where(Ride.destination.ilike(f"%{destination.strip()}%"))
    if travel_date:
        stmt = stmt.where(Ride.travel_date == travel_date)
    return list(db.scalars(stmt.order_by(Ride.travel_date, Ride.departure_time).limit(100)).all())

@router.get("/{ride_id}", response_model=RideOut)
def get_ride(ride_id: int, db: Session = Depends(get_db)):
    ride = db.get(Ride, ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    return ride

@router.patch("/{ride_id}", response_model=RideOut)
def update_ride(
    ride_id: int,
    payload: RideUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("rider")),
):
    ride = db.get(Ride, ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    if ride.rider_id != user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own rides")
    updates = payload.model_dump(exclude_unset=True)
    if "travel_date" in updates and updates["travel_date"] and updates["travel_date"] < date.today():
        raise HTTPException(status_code=422, detail="Travel date cannot be in the past")
    if "total_seats" in updates:
        confirmed = sum(
            b.seats_requested for b in ride.bookings if b.status == "CONFIRMED"
        )
        if updates["total_seats"] < confirmed:
            raise HTTPException(status_code=409, detail="Total seats cannot be less than confirmed bookings")
        ride.available_seats = updates["total_seats"] - confirmed
    for key, value in updates.items():
        if key != "total_seats":
            setattr(ride, key, value.strip() if isinstance(value, str) and key in ("pickup", "destination") else value)
    db.commit()
    db.refresh(ride)
    return ride

@router.delete("/{ride_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ride(
    ride_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("rider")),
):
    ride = db.get(Ride, ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    if ride.rider_id != user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own rides")
    if any(b.status == "CONFIRMED" for b in ride.bookings):
        raise HTTPException(status_code=409, detail="Cannot delete a ride with confirmed bookings")
    ride.status = "CANCELLED"
    db.commit()
    return None

@router.get("/{ride_id}/bookings", response_model=list[BookingOut])
def ride_bookings(
    ride_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("rider")),
):
    ride = db.get(Ride, ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    if ride.rider_id != user.id:
        raise HTTPException(status_code=403, detail="You can only view bookings for your own rides")
    return list(db.scalars(select(Booking).where(Booking.ride_id == ride_id).order_by(Booking.created_at.desc())).all())
