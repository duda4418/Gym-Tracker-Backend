from fastapi import APIRouter, Depends

from app.api.dependencies import get_auth_service, get_current_user
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    SignupRequest,
    TokenPairResponse,
)
from app.schemas.users import AuthenticatedUser, UserResponse
from app.services.auth_service import AuthService

auth_router = APIRouter(tags=["Authentication"])


@auth_router.post("/auth/signup", response_model=UserResponse, status_code=201)
async def signup(user_data: SignupRequest, auth_service: AuthService = Depends(get_auth_service)):
    return await auth_service.signup(user_data.email, user_data.password, user_data.name)


@auth_router.post("/auth/login", response_model=TokenPairResponse)
async def login(user_data: LoginRequest, auth_service: AuthService = Depends(get_auth_service)):
    return await auth_service.login(user_data.email, user_data.password)


@auth_router.post("/auth/refresh", response_model=TokenPairResponse)
async def refresh_tokens(data: RefreshTokenRequest, auth_service: AuthService = Depends(get_auth_service)):
    return await auth_service.refresh_tokens(data.refresh_token)


@auth_router.get("/auth/me", response_model=UserResponse)
async def get_me(
    current_user: AuthenticatedUser = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.me(current_user.id)


@auth_router.post("/auth/logout")
async def logout(
    data: LogoutRequest | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    refresh_token = data.refresh_token if data else None
    return await auth_service.logout(current_user.id, refresh_token)
