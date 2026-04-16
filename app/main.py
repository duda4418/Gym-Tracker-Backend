import os
from time import perf_counter

from fastapi import FastAPI
from fastapi import Request
from opentelemetry import trace
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.routers.auth import auth_router
from app.api.routers.muscles import muscles_router
from app.api.routers.exercises import exercises_router
from app.api.routers.splits import splits_router
from app.api.routers.users import qrcode_router
from app.api.routers.workout_sessions import workout_sessions_router
from app.api.routers.workouts import workouts_router
from app.api.routers.favourites import favorites_router
from app.core.config import get_settings
from app.core.log_config import (
    configure_logging,
    get_app_logger,
    sanitize_request_scope,
)
from app.core.profiling import configure_profiling
from app.core.telemetry import configure_telemetry
from app.utils.errors.database import DatabaseUnavailableError

settings = get_settings()
configure_logging(settings)
configure_profiling(settings)
logger = get_app_logger()
app = FastAPI()

Instrumentator().instrument(app).expose(app)
configure_telemetry(app, settings)

@app.exception_handler(DatabaseUnavailableError)
async def handle_database_unavailable(_, exc: DatabaseUnavailableError):
    return JSONResponse(status_code=503, content={"detail": exc.detail})

os.makedirs(settings.UPLOADS_DIR, exist_ok=True)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = perf_counter()
    client_host = request.client.host if request.client else None
    safe_base_url = str(request.base_url).rstrip("/")

    try:
        response = await call_next(request)
    except Exception:
        safe_path = sanitize_request_scope(request)
        current_span = trace.get_current_span()
        if current_span.is_recording():
            current_span.set_attribute("http.target", safe_path)
            current_span.set_attribute("http.route", safe_path)
            current_span.set_attribute("url.path", safe_path)
            current_span.set_attribute("url.query", "")
            current_span.set_attribute("http.url", f"{safe_base_url}{safe_path}")
        duration_ms = round((perf_counter() - start) * 1000, 2)
        logger.exception(
            "Unhandled request error",
            extra={
                "method": request.method,
                "path": safe_path,
                "status_code": 500,
                "duration_ms": duration_ms,
                "client_host": client_host,
            },
        )
        raise

    safe_path = sanitize_request_scope(request)
    current_span = trace.get_current_span()
    if current_span.is_recording():
        current_span.set_attribute("http.target", safe_path)
        current_span.set_attribute("http.route", safe_path)
        current_span.set_attribute("url.path", safe_path)
        current_span.set_attribute("url.query", "")
        current_span.set_attribute("http.url", f"{safe_base_url}{safe_path}")
    duration_ms = round((perf_counter() - start) * 1000, 2)
    logger.info(
        "Request completed",
        extra={
            "method": request.method,
            "path": safe_path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "client_host": client_host,
        },
    )
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://192.168.1.11:3000",
                   "http://localhost:3001", "http://192.168.1.11:3001",
                   "http://localhost:3002", "http://192.168.1.11:3002",
                   "http://localhost:3003", "http://192.168.1.11:3003",
                   "http://localhost:3004", "http://192.168.1.11:3004",
                   "http://10.11.8.231:3000",
                   "http://10.11.8.231:3001",
                   "https://gym-tracker-hempvie8u-davidrotarius-projects.vercel.app",
                   "https://gym-tracker-topaz.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded images as static files
app.mount("/uploads", StaticFiles(directory=settings.UPLOADS_DIR), name="uploads")

app.include_router(muscles_router)
app.include_router(exercises_router)
app.include_router(splits_router)
app.include_router(workouts_router)
app.include_router(workout_sessions_router)
app.include_router(auth_router)
app.include_router(qrcode_router)
app.include_router(favorites_router)

@app.get("/")
def health_check():
    return {"status": "ok"}
