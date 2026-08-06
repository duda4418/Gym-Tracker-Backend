from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
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
from app.schemas.users import AuthenticatedUser
from app.services.auth_service import AuthService
from app.services.exercise_service import ExerciseService
from app.services.favorite_service import FavoriteService
from app.services.muscle_service import MuscleService
from app.services.profile_service import ProfileService
from app.services.qr_service import QRService
from app.services.split_service import SplitService
from app.services.workout_service import WorkoutService

bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service(session: Session = Depends(get_db_session)) -> AuthService:
    return AuthService(AuthRepository(session))


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthenticatedUser:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    return await auth_service.authenticate_access_token(credentials.credentials)


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
    return WorkoutService(
        WorkoutRepository(session),
        UserRepository(session),
        ExerciseRepository(session),
        SplitRepository(session),
    )


def get_favorite_service(session: Session = Depends(get_db_session)) -> FavoriteService:
    return FavoriteService(
        FavoriteRepository(session),
        ExerciseRepository(session),
        UserRepository(session),
    )


def get_qr_service(session: Session = Depends(get_db_session)) -> QRService:
    return QRService(QRRepository(session))


def get_profile_service(session: Session = Depends(get_db_session)) -> ProfileService:
    return ProfileService(UserRepository(session))
