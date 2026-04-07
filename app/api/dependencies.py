from fastapi import Depends, Header, HTTPException
import jwt
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.repositories.auth_repository import AuthRepository
from app.repositories.exercise_repository import ExerciseRepository
from app.repositories.favorite_repository import FavoriteRepository
from app.repositories.muscle_repository import MuscleRepository
from app.repositories.qr_repository import QRRepository
from app.repositories.split_repository import SplitRepository
from app.repositories.user_repository import UserRepository
from app.repositories.workout_repository import WorkoutRepository
from app.repositories.workout_session_repository import WorkoutSessionRepository
from app.services.auth_service import AuthService
from app.services.exercise_service import ExerciseService
from app.services.favorite_service import FavoriteService
from app.services.muscle_service import MuscleService
from app.services.qr_service import QRService
from app.services.split_service import SplitService
from app.services.workout_service import WorkoutService
from app.services.workout_session_service import WorkoutSessionService
from app.utils.auth import decode_access_token


def get_current_user(authorization: str = Header(None)):
    if not authorization or "Bearer " not in authorization:
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ")[1]
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    auth_id = payload.get("sub")
    if not auth_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    return {"id": auth_id}


def get_auth_service(session: Session = Depends(get_db_session)) -> AuthService:
    return AuthService(AuthRepository(session))


def get_muscle_service(session: Session = Depends(get_db_session)) -> MuscleService:
    return MuscleService(MuscleRepository(session))


def get_exercise_service(session: Session = Depends(get_db_session)) -> ExerciseService:
    return ExerciseService(
        ExerciseRepository(session),
        MuscleRepository(session),
        UserRepository(session),
        FavoriteRepository(session),
    )


def get_split_service(session: Session = Depends(get_db_session)) -> SplitService:
    return SplitService(SplitRepository(session), UserRepository(session), MuscleRepository(session))


def get_workout_service(session: Session = Depends(get_db_session)) -> WorkoutService:
    return WorkoutService(WorkoutRepository(session), UserRepository(session), ExerciseRepository(session))


def get_workout_session_service(session: Session = Depends(get_db_session)) -> WorkoutSessionService:
    return WorkoutSessionService(WorkoutSessionRepository(session), MuscleRepository(session))


def get_favorite_service(session: Session = Depends(get_db_session)) -> FavoriteService:
    return FavoriteService(
        FavoriteRepository(session),
        ExerciseRepository(session),
        MuscleRepository(session),
        UserRepository(session),
    )


def get_qr_service(session: Session = Depends(get_db_session)) -> QRService:
    return QRService(QRRepository(session))
