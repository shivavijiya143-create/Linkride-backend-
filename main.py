from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.config import FRONTEND_ORIGINS
from app.database import Base, engine
from app import models  # noqa: F401 - ensure models are registered
from app.routers import auth, rides, bookings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Convenient for a starter/demo. Use Alembic migrations for production.
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="LinkRide API",
    description="Commute-sharing backend for the LinkRide project",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(rides.router)
app.include_router(bookings.router)

@app.get("/")
def home():
    return {"name": "LinkRide API", "status": "running", "docs": "/docs"}

@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"api": "online", "database": "connected"}
    except SQLAlchemyError:
        return {"api": "online", "database": "unavailable"}
