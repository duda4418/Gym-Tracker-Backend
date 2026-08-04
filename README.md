# Gym Tracker Backend

A clean FastAPI backend for a gym tracking app. It handles authentication, exercise management, workout logging, and user-specific training data, with PostgreSQL persistence and built-in observability.

## Main features

- JWT authentication
- Exercise and muscle management
- Workout splits and workout sessions
- Workout logging and history
- Favorite exercises
- QR code upload for users
- Database migrations with Alembic
- Metrics, tracing, logging, and profiling support

## Tech stack

- **Backend:** FastAPI, Python
- **Database:** PostgreSQL, SQLAlchemy, Alembic
- **Auth:** JWT, Passlib
- **Server:** Uvicorn
- **Testing:** Pytest
- **Observability:** Prometheus, Grafana, OpenTelemetry, Loki, Tempo, Pyroscope
- **Containerization:** Docker, Docker Compose

## Observability stack

- **Prometheus** - collects application metrics such as request counts, latency, and error rates
- **Grafana** - visualizes metrics, logs, traces, alerts, and profiles in dashboards
- **Alertmanager** - handles alerts fired by Prometheus and routes notifications
- **OpenTelemetry** - standard used to generate traces from the backend
- **OTel Collector** - receives telemetry from the app and forwards it to the right backends
- **Tempo** - stores and lets you search distributed traces
- **Loki** - stores application logs
- **Promtail** - reads log files and ships them to Loki
- **Pyroscope** - collects continuous profiling data to analyze performance hotspots

## Project structure

```text
Gym-Tracker-Backend/
├── app/
│   ├── api/            # Routers and dependencies
│   ├── core/           # Settings, logging, telemetry, profiling
│   ├── db/             # Database session and models
│   ├── repositories/   # Data access layer
│   ├── schemas/        # Pydantic request/response models
│   ├── services/       # Business logic
│   ├── tests/          # Test suite
│   └── main.py         # FastAPI entrypoint
├── alembic/            # Database migrations
├── deploy/             # Deployment-related files
├── docker-compose.local.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Quick start

### 1. Configure environment

Copy `.env.example` to `.env` and update the values you need.

### 2. Run locally with Docker

```powershell
cd C:\Users\daserban\PycharmProjects\Gym-Tracker-Backend
docker compose -f docker-compose.local.yml up -d --build postgres backend
```

The backend container applies Alembic migrations before starting. The
observability services are optional and are not required for local API work.

Backend: `http://localhost:8000`

### 3. Useful endpoints

- Health check: `GET /`
- API docs: `GET /docs`
- Metrics: `GET /metrics`

## Core API areas

- `auth` - signup, login, refresh, logout, current user
- `muscles` - create and list muscles
- `exercises` - create, list, bulk import, filter by muscle
- `splits` - manage training splits
- `workouts` - start sessions, add exercises and sets, and review history
- `favorites` - save favorite exercises
- `users` - QR code upload and retrieval

## Best practices

- Keep secrets only in `.env` or your deployment secret store
- Run migrations before starting the app in new environments
- Use the `services/` layer for business logic and `repositories/` for database access
- Add tests for new endpoints and service behavior
- Keep observability enabled in Docker for easier debugging

## Development notes

- The app entrypoint is `app/main.py`
- Static uploads are served from `app/uploads`
- Seed/import utilities live in `app/scripts/`
- Local monitoring is available through the Docker stack when needed

