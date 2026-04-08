from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
import jwt

from app.schemas.auth import TokenPairResponse
from app.schemas.users import AuthenticatedUser, UserResponse
from app.repositories.auth_repository import AuthRepository
from app.utils.auth import (
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)


class AuthService:
    def __init__(self, repo: AuthRepository) -> None:
        self.repo = repo

    async def signup(self, email: str, password: str, name: str) -> UserResponse:
        existing = self.repo.get_by_email(email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        password_hash = hash_password(password)
        user = self.repo.create_user(email=email, name=name, password_hash=password_hash)
        return UserResponse(id=user.id, email=user.email, name=user.name)

    async def login(self, email: str, password: str) -> TokenPairResponse:
        user = self.repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        return self._issue_tokens(user)

    async def refresh_tokens(self, refresh_token: str) -> TokenPairResponse:
        user = self._get_user_from_token(refresh_token, expected_type=REFRESH_TOKEN_TYPE)
        if user.refresh_token_hash != hash_token(refresh_token):
            raise HTTPException(status_code=401, detail="Refresh token has been revoked")
        if user.refresh_token_expires_at and user.refresh_token_expires_at <= datetime.now(timezone.utc):
            self.repo.clear_refresh_token(user)
            raise HTTPException(status_code=401, detail="Refresh token has expired")

        return self._issue_tokens(user)

    async def me(self, user_id) -> UserResponse:
        db_user = self.repo.get_by_id(user_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        return UserResponse(id=db_user.id, email=db_user.email, name=db_user.name)

    async def authenticate_access_token(self, token: str) -> AuthenticatedUser:
        db_user = self._get_user_from_token(token)
        return AuthenticatedUser(id=db_user.id, email=db_user.email, name=db_user.name)

    async def logout(self, user_id, refresh_token: str | None = None) -> dict:
        db_user = self.repo.get_by_id(user_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        if refresh_token:
            try:
                payload = decode_token(refresh_token, expected_type=REFRESH_TOKEN_TYPE)
            except jwt.PyJWTError:
                raise HTTPException(status_code=401, detail="Invalid refresh token")

            token_subject = self._parse_user_id(payload.get("sub"))
            if token_subject != db_user.id or db_user.refresh_token_hash != hash_token(refresh_token):
                raise HTTPException(status_code=401, detail="Refresh token has been revoked")

        self.repo.clear_refresh_token(db_user)
        return {"message": "User logged out successfully"}

    def _issue_tokens(self, user) -> TokenPairResponse:
        access_token = create_access_token(str(user.id))
        refresh_token, refresh_expires_at = create_refresh_token(str(user.id))
        self.repo.save_refresh_token(user, hash_token(refresh_token), refresh_expires_at)
        return TokenPairResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    def _get_user_from_token(self, token: str, expected_type: str | None = None):
        try:
            payload = decode_access_token(token) if expected_type is None else decode_token(token, expected_type=expected_type)
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

        token_subject = payload.get("sub")
        if not token_subject:
            raise HTTPException(status_code=401, detail="Invalid token")

        user_id = self._parse_user_id(token_subject)
        db_user = self.repo.get_by_id(user_id)
        if not db_user:
            raise HTTPException(status_code=401, detail="User not found")

        if expected_type == REFRESH_TOKEN_TYPE and not db_user.refresh_token_hash:
            raise HTTPException(status_code=401, detail="Refresh token has been revoked")

        return db_user

    @staticmethod
    def _parse_user_id(raw_user_id: str) -> UUID:
        try:
            return UUID(raw_user_id)
        except (TypeError, ValueError):
            raise HTTPException(status_code=401, detail="Invalid token")
