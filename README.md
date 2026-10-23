# LinkRide Backend (FastAPI + MySQL)

Starter backend for the LinkRide commute-sharing college project.

## Included
- FastAPI app and interactive API docs
- MySQL connection via SQLAlchemy
- User registration/login with Argon2 password hashing and JWT bearer tokens
- Ride create/list/detail/update/delete (owner-only edits)
- Booking requests, owner approval/rejection, passenger cancellation
- Seat-capacity checks and transactional booking updates
- CORS configuration for your frontend
- Demo-friendly local setup instructions

**Important:** This is a starter project, not a production-audited ride service. Before real public use, add automated tests, rate limiting, email/phone verification, monitoring, backups, migration management (Alembic), privacy/legal review, and review security settings.

## Requirements
- Python 3.11+
- MySQL 8+ (or compatible MySQL server)

## 1. Create database and user
Run in MySQL Workbench or the MySQL command line (change the password):

```sql
CREATE DATABASE linkride_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'linkride_app'@'localhost' IDENTIFIED BY 'CHANGE_ME_TO_A_STRONG_PASSWORD';
GRANT ALL PRIVILEGES ON linkride_db.* TO 'linkride_app'@'localhost';
```

If the database/user already exists, do not blindly rerun CREATE statements. Use your existing credentials.

## 2. Configure environment
Copy `.env.example` to `.env` and update `DATABASE_URL` with your real MySQL username/password/host.
Set `JWT_SECRET` to a long random secret. Do not commit `.env` to GitHub.

Example:
`mysql+pymysql://linkride_app:YOUR_PASSWORD@localhost:3306/linkride_db`

For a password containing reserved URL characters, URL-encode those characters.

## 3. Install and run

Windows PowerShell:
```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Edit `.env` before using endpoints that access MySQL. The API starts at `http://127.0.0.1:8000`.
- `http://127.0.0.1:8000/docs` — test API endpoints
- `http://127.0.0.1:8000/health` — API/database health

On startup, this starter creates tables with SQLAlchemy `create_all`. Use Alembic migrations before evolving a production database.

## 4. Main endpoints
- `POST /api/auth/register` — register user (`passenger` or `rider`)
- `POST /api/auth/login` — OAuth2 form login; use Swagger's form fields `username` (email) and `password`
- `GET /api/auth/me` — current authenticated user
- `POST /api/rides` — create ride (rider only)
- `GET /api/rides` — search by `pickup`, `destination`, optional `travel_date`
- `GET /api/rides/{ride_id}` — ride details
- `PATCH /api/rides/{ride_id}` — edit own ride
- `DELETE /api/rides/{ride_id}` — delete own ride if no confirmed bookings
- `POST /api/bookings` — passenger requests seats
- `GET /api/bookings/my` — list current user's bookings
- `GET /api/rides/{ride_id}/bookings` — rider views bookings for their ride
- `PATCH /api/bookings/{booking_id}` — ride owner approves/rejects pending booking
- `POST /api/bookings/{booking_id}/cancel` — passenger cancels pending/confirmed booking

Booking approval and cancellation lock the ride row while adjusting available seats. For production, review database isolation and locking behavior with your exact MySQL configuration.

## 5. Frontend integration
Set `FRONTEND_ORIGINS` to the exact origin(s) your frontend uses. GitHub Pages origins are like `https://USERNAME.github.io` (origin only, not repository path). Set the frontend's API base URL to your deployed backend URL; never put database credentials or JWT secrets in frontend JavaScript.

The demo frontend can call endpoints with `fetch`. For protected endpoints:
`Authorization: Bearer <access_token>`

## 6. Notes
- Currency/fare is stored as a decimal amount; this starter does not process payments.
- Ride search is text-based; no live GPS/map routing is included.
- Authentication is basic email/password + JWT; add refresh-token/revocation strategy before production.
- Use a hosted MySQL service with TLS and network restrictions for online deployment.
