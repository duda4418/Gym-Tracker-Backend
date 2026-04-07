from fastapi import HTTPException
import jwt

from app.schemas.auth import UserResponse
from app.repositories.auth_repository import AuthRepository
from app.utils.auth import create_access_token, decode_access_token, hash_password, verify_password


class AuthService:
    def __init__(self, repo: AuthRepository) -> None:
        self.repo = repo

    async def signup(self, email: str, password: str, name: str) -> UserResponse:
        existing = self.repo.get_by_email(email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        password_hash = hash_password(password)
        user = self.repo.create_user(auth_id=email, email=email, name=name, password_hash=password_hash)
        return UserResponse(id=user.id, email=user.email, name=user.name)

    async def login(self, email: str, password: str) -> dict:
        user = self.repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        access_token = create_access_token(str(user.auth_id))
        return {
            "access_token": access_token,
            "refresh_token": None,
            "token_type": "bearer",
        }

    async def me(self, token: str) -> UserResponse:
        try:
            payload = decode_access_token(token)
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

        auth_id = payload.get("sub")
        if not auth_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        db_user = self.repo.get_by_auth_id(auth_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        return UserResponse(id=db_user.id, email=db_user.email, name=db_user.name)

    async def logout(self, token: str) -> dict:
        return {"message": "User logged out successfully"}
