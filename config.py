import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
FRONTEND_ORIGINS = [
    item.strip()
    for item in os.getenv(
        "FRONTEND_ORIGINS",
        "http://127.0.0.1:5500,http://localhost:5500",
    ).split(",")
    if item.strip()
]
