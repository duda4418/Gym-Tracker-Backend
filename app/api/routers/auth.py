from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.dependencies import get_auth_service
from app.schemas.auth import UserLogin, UserResponse, UserSignup
from app.services.auth_service import AuthService

auth_router = APIRouter(tags=["Authentication"])

@auth_router.post("/auth/signup", response_model=UserResponse)
async def signup(user_data: UserSignup, auth_service: AuthService = Depends(get_auth_service)):
    return await auth_service.signup(user_data.email, user_data.password, user_data.name)


@auth_router.post("/auth/login")
async def login(user_data: UserLogin, auth_service: AuthService = Depends(get_auth_service)):
    return await auth_service.login(user_data.email, user_data.password)


@auth_router.get("/auth/me", response_model=UserResponse)
async def get_current_user(authorization: str = Header(None), auth_service: AuthService = Depends(get_auth_service)):
    if not authorization or "Bearer " not in authorization:
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ")[1]
    return await auth_service.me(token)


@auth_router.post("/auth/logout")
async def logout(authorization: str = Header(None), auth_service: AuthService = Depends(get_auth_service)):
    if not authorization or "Bearer " not in authorization:
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ")[1]
    return await auth_service.logout(token)
