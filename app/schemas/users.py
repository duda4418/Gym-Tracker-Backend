from uuid import UUID

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str | None = None
    profile_pic: str | None = None


class AuthenticatedUser(UserResponse):
    pass

