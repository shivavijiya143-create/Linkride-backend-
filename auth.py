from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import RegisterIn, UserOut, TokenOut
from app.security import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = str(payload.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = User(
        full_name=payload.full_name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        phone=payload.phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=TokenOut)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    email = form.username.lower().strip()
    user = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return {"access_token": create_access_token(user.id), "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
