import os

from fastapi import FastAPI
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
from app.utils.errors.database import DatabaseUnavailableError

settings = get_settings()
app = FastAPI()

Instrumentator().instrument(app).expose(app)

@app.exception_handler(DatabaseUnavailableError)
async def handle_database_unavailable(_, exc: DatabaseUnavailableError):
    return JSONResponse(status_code=503, content={"detail": exc.detail})

os.makedirs(settings.UPLOADS_DIR, exist_ok=True)


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

# ✅ Serve uploaded images as static files
app.mount("/uploads", StaticFiles(directory=settings.UPLOADS_DIR), name="uploads")

# ✅ Register Routers
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
